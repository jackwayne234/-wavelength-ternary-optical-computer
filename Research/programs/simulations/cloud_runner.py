#!/usr/bin/env python3
"""
Cloud Runner for MEEP Simulations (AWS EC2)

Spins up an AWS EC2 instance, runs MEEP simulations with MPI,
downloads results, and terminates the instance.

Usage:
    python cloud_runner.py --sim kerr_resonator_sim.py --cores 64
    python cloud_runner.py --sim mzi_switch_sim.py --cores 96 --ram 768
    python cloud_runner.py --list-servers  # Show available instance types
    python cloud_runner.py --spot          # Use spot instances (60-70% cheaper)

Setup:
    1. Install AWS CLI: https://aws.amazon.com/cli/
    2. Configure credentials: aws configure
    3. Create a key pair in EC2 console and download the .pem file
    4. Set environment variable: export AWS_KEY_PATH="~/.ssh/your-key.pem"
    5. Set key name: export AWS_KEY_NAME="your-key-name"

Requirements:
    pip install boto3 paramiko scp
"""

import argparse
import os
import sys
import time
from pathlib import Path

try:
    import boto3
    import paramiko
    from scp import SCPClient
except ImportError:
    print("Missing dependencies. Install with:")
    print("  pip install boto3 paramiko scp")
    sys.exit(1)


# Project paths
PROJECT_ROOT = Path(__file__).parent.parent.parent.parent  # Optical_computing/
SIMULATIONS_DIR = Path(__file__).parent
DATA_DIR = PROJECT_ROOT / "Research" / "data"

# AWS EC2 instance types optimized for compute + high memory
# Using R7i (Intel) and R7a (AMD) for high memory + good compute
INSTANCE_TYPES = {
    "medium": {
        "type": "r7i.8xlarge",
        "vcpus": 32,
        "ram_gb": 256,
        "cost_hr_ondemand": 2.02,
        "cost_hr_spot": 0.70,
    },
    "large": {
        "type": "r7i.16xlarge",
        "vcpus": 64,
        "ram_gb": 512,
        "cost_hr_ondemand": 4.03,
        "cost_hr_spot": 1.40,
    },
    "xlarge": {
        "type": "r7i.24xlarge",
        "vcpus": 96,
        "ram_gb": 768,
        "cost_hr_ondemand": 6.05,
        "cost_hr_spot": 2.10,
    },
    "max": {
        "type": "r7i.48xlarge",
        "vcpus": 192,
        "ram_gb": 1536,
        "cost_hr_ondemand": 12.10,
        "cost_hr_spot": 4.20,
    },
    # AMD EPYC options (sometimes cheaper)
    "amd-large": {
        "type": "r7a.16xlarge",
        "vcpus": 64,
        "ram_gb": 512,
        "cost_hr_ondemand": 3.62,
        "cost_hr_spot": 1.25,
    },
    "amd-xlarge": {
        "type": "r7a.24xlarge",
        "vcpus": 96,
        "ram_gb": 768,
        "cost_hr_ondemand": 5.44,
        "cost_hr_spot": 1.90,
    },
}

# Default region
AWS_REGION = os.environ.get("AWS_REGION", "us-east-1")

# Ubuntu 22.04 LTS AMI IDs by region (update as needed)
UBUNTU_AMIS = {
    "us-east-1": "ami-0c7217cdde317cfec",
    "us-east-2": "ami-05fb0b8c1424f266b",
    "us-west-1": "ami-0ce2cb35386fc22e9",
    "us-west-2": "ami-008fe2fc65df48dac",
    "eu-west-1": "ami-0905a3c97561e0b69",
    "eu-central-1": "ami-0faab6bdbac9486fb",
}


def get_config():
    """Get AWS configuration from environment."""
    key_path = os.environ.get("AWS_KEY_PATH")
    key_name = os.environ.get("AWS_KEY_NAME")

    if not key_path or not key_name:
        print("Error: AWS key configuration not set")
        print("\nTo set up:")
        print("  1. Go to AWS EC2 Console -> Key Pairs")
        print("  2. Create a new key pair and download the .pem file")
        print("  3. Run:")
        print('     export AWS_KEY_PATH="~/.ssh/your-key.pem"')
        print('     export AWS_KEY_NAME="your-key-name"')
        print("")
        print("  Also make sure AWS CLI is configured:")
        print("     aws configure")
        sys.exit(1)

    key_path = os.path.expanduser(key_path)
    if not os.path.exists(key_path):
        print(f"Error: Key file not found: {key_path}")
        sys.exit(1)

    return key_path, key_name


def get_or_create_security_group(ec2_client) -> str:
    """Get or create a security group that allows SSH."""
    sg_name = "meep-simulation-sg"

    try:
        response = ec2_client.describe_security_groups(GroupNames=[sg_name])
        return response["SecurityGroups"][0]["GroupId"]
    except ec2_client.exceptions.ClientError:
        pass

    # Create new security group
    print(f"Creating security group '{sg_name}'...")
    response = ec2_client.create_security_group(
        GroupName=sg_name,
        Description="Security group for MEEP simulations - allows SSH"
    )
    sg_id = response["GroupId"]

    # Allow SSH from anywhere (you may want to restrict this)
    ec2_client.authorize_security_group_ingress(
        GroupId=sg_id,
        IpPermissions=[{
            "IpProtocol": "tcp",
            "FromPort": 22,
            "ToPort": 22,
            "IpRanges": [{"CidrIp": "0.0.0.0/0"}]
        }]
    )

    return sg_id


def select_instance_type(cores: int, ram_gb: int) -> dict:
    """Select appropriate instance type based on requirements."""
    for name, spec in INSTANCE_TYPES.items():
        if spec["vcpus"] >= cores and spec["ram_gb"] >= ram_gb:
            return spec
    return INSTANCE_TYPES["max"]


def create_instance(ec2_client, ec2_resource, instance_type: str, key_name: str, use_spot: bool, region: str) -> tuple:
    """Create a new EC2 instance."""
    print(f"Creating {'spot' if use_spot else 'on-demand'} instance (type: {instance_type})...")

    sg_id = get_or_create_security_group(ec2_client)
    ami_id = UBUNTU_AMIS.get(region)

    if not ami_id:
        print(f"Error: No AMI configured for region {region}")
        print(f"Available regions: {list(UBUNTU_AMIS.keys())}")
        sys.exit(1)

    instance_params = {
        "ImageId": ami_id,
        "InstanceType": instance_type,
        "KeyName": key_name,
        "SecurityGroupIds": [sg_id],
        "MinCount": 1,
        "MaxCount": 1,
        "BlockDeviceMappings": [{
            "DeviceName": "/dev/sda1",
            "Ebs": {
                "VolumeSize": 100,  # 100GB root volume
                "VolumeType": "gp3",
                "DeleteOnTermination": True
            }
        }],
        "TagSpecifications": [{
            "ResourceType": "instance",
            "Tags": [{"Key": "Name", "Value": "meep-simulation"}]
        }]
    }

    if use_spot:
        instance_params["InstanceMarketOptions"] = {
            "MarketType": "spot",
            "SpotOptions": {
                "SpotInstanceType": "one-time",
                "InstanceInterruptionBehavior": "terminate"
            }
        }

    response = ec2_client.run_instances(**instance_params)
    instance_id = response["Instances"][0]["InstanceId"]

    print(f"Instance {instance_id} created. Waiting for it to be running...")

    # Wait for instance to be running
    instance = ec2_resource.Instance(instance_id)
    instance.wait_until_running()
    instance.reload()

    ip = instance.public_ip_address
    print(f"Instance ready at {ip}")

    # Wait for SSH to be available
    print("Waiting for SSH to be ready...")
    time.sleep(45)

    return instance, ip


def ssh_connect(ip: str, key_path: str, retries: int = 10) -> paramiko.SSHClient:
    """Connect to instance via SSH."""
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    key = paramiko.RSAKey.from_private_key_file(key_path)

    for i in range(retries):
        try:
            ssh.connect(ip, username="ubuntu", pkey=key, timeout=30)
            return ssh
        except Exception as e:
            if i < retries - 1:
                print(f"SSH connection failed, retrying ({i+1}/{retries})...")
                time.sleep(15)
            else:
                raise e
    return ssh


def run_command(ssh: paramiko.SSHClient, cmd: str, show_output: bool = True) -> str:
    """Run command on remote instance."""
    if show_output:
        print(f"  $ {cmd}")
    stdin, stdout, stderr = ssh.exec_command(cmd, timeout=3600)
    output = stdout.read().decode()
    error = stderr.read().decode()
    if show_output and output:
        print(output)
    if error and "WARNING" not in error:
        print(f"  stderr: {error}")
    return output


def setup_meep(ssh: paramiko.SSHClient, cores: int):
    """Install MEEP and dependencies on the instance."""
    print("\nInstalling MEEP and dependencies (this takes a few minutes)...")

    commands = [
        "sudo apt update",
        "sudo apt install -y python3-pip python3-venv libopenmpi-dev openmpi-bin",
        "sudo apt install -y python3-meep python3-h5py h5utils python3-matplotlib python3-numpy",
    ]

    for cmd in commands:
        run_command(ssh, cmd, show_output=False)

    print("MEEP installation complete.")


def upload_simulation(ssh: paramiko.SSHClient, ip: str, key_path: str, sim_file: str):
    """Upload simulation file and dependencies to the instance."""
    print(f"\nUploading simulation: {sim_file}")

    # Create working directory
    run_command(ssh, "mkdir -p ~/simulation", show_output=False)

    key = paramiko.RSAKey.from_private_key_file(key_path)

    # Upload files via SCP
    with SCPClient(ssh.get_transport()) as scp:
        # Upload main simulation file
        sim_path = SIMULATIONS_DIR / sim_file
        if not sim_path.exists():
            print(f"Error: Simulation file not found: {sim_path}")
            sys.exit(1)
        scp.put(str(sim_path), "~/simulation/")

        # Upload shared components if they exist
        shared_dir = SIMULATIONS_DIR.parent / "shared_components"
        if shared_dir.exists():
            run_command(ssh, "mkdir -p ~/simulation/shared_components", show_output=False)
            for f in shared_dir.glob("*.py"):
                scp.put(str(f), "~/simulation/shared_components/")

    print("Upload complete.")


def run_simulation(ssh: paramiko.SSHClient, sim_file: str, cores: int, extra_args: str = ""):
    """Run the MEEP simulation with MPI."""
    print(f"\nRunning simulation with {cores} cores...")
    print("-" * 60)

    # Use slightly fewer cores than available to leave room for OS
    effective_cores = max(1, cores - 2)

    cmd = f"cd ~/simulation && mpirun --use-hwthread-cpus -np {effective_cores} python3 -u {sim_file} {extra_args}"

    # Run with real-time output
    stdin, stdout, stderr = ssh.exec_command(cmd, timeout=86400)  # 24 hour timeout

    # Stream output
    while True:
        line = stdout.readline()
        if not line:
            break
        print(line, end="")

    # Check for errors
    error = stderr.read().decode()
    if error and "WARNING" not in error:
        print(f"\nErrors:\n{error}")

    print("-" * 60)
    print("Simulation complete.")


def download_results(ssh: paramiko.SSHClient, ip: str, key_path: str, sim_file: str) -> Path:
    """Download simulation results from the instance."""
    print("\nDownloading results...")

    # Create local output directory
    sim_name = Path(sim_file).stem
    output_dir = DATA_DIR / "cloud_results" / sim_name
    output_dir.mkdir(parents=True, exist_ok=True)

    with SCPClient(ssh.get_transport()) as scp:
        # Download all output files
        for ext in ["*.h5", "*.csv", "*.png", "*.npy", "*.txt"]:
            try:
                run_command(ssh, f"ls ~/simulation/{ext} 2>/dev/null", show_output=False)
                scp.get(f"~/simulation/{ext}", str(output_dir))
            except Exception:
                pass  # No files with this extension

    print(f"Results saved to: {output_dir}")
    return output_dir


def terminate_instance(ec2_resource, instance):
    """Terminate the EC2 instance."""
    print("\nTerminating instance...")
    instance.terminate()
    print("Instance terminated. No more charges.")


def list_servers():
    """Print available instance configurations."""
    print("\nAvailable AWS EC2 Instance Types for MEEP:")
    print("-" * 80)
    print(f"{'Name':<12} {'Type':<16} {'vCPUs':<8} {'RAM':<10} {'On-Demand':<12} {'Spot':<10}")
    print("-" * 80)
    for name, spec in INSTANCE_TYPES.items():
        print(f"{name:<12} {spec['type']:<16} {spec['vcpus']:<8} {spec['ram_gb']}GB{'':<4} ${spec['cost_hr_ondemand']:.2f}/hr{'':<4} ${spec['cost_hr_spot']:.2f}/hr")
    print("-" * 80)
    print("\nRecommended for 81x81 PE TPU simulation:")
    print("  python cloud_runner.py --sim your_sim.py --cores 64 --ram 512 --spot")
    print("\nSpot instances are 60-70% cheaper but can be interrupted (rare).")


def estimate_cost(instance_spec: dict, use_spot: bool, hours: float = 1.0) -> str:
    """Estimate cost for running the simulation."""
    rate = instance_spec["cost_hr_spot"] if use_spot else instance_spec["cost_hr_ondemand"]
    cost = rate * hours
    return f"${cost:.2f} for {hours}hr (${rate:.2f}/hr)"


def main():
    parser = argparse.ArgumentParser(description="Run MEEP simulations on AWS EC2")
    parser.add_argument("--sim", type=str, help="Simulation file to run (e.g., kerr_resonator_sim.py)")
    parser.add_argument("--cores", type=int, default=64, help="Number of vCPUs (default: 64)")
    parser.add_argument("--ram", type=int, default=512, help="RAM in GB (default: 512)")
    parser.add_argument("--args", type=str, default="", help="Extra arguments to pass to simulation")
    parser.add_argument("--spot", action="store_true", help="Use spot instances (cheaper, can be interrupted)")
    parser.add_argument("--list-servers", action="store_true", help="List available instance types")
    parser.add_argument("--keep-instance", action="store_true", help="Don't terminate instance after simulation")
    parser.add_argument("--region", type=str, default=AWS_REGION, help=f"AWS region (default: {AWS_REGION})")

    args = parser.parse_args()

    if args.list_servers:
        list_servers()
        return

    if not args.sim:
        parser.print_help()
        print("\n" + "="*60)
        print("Example for your 81x81 PE TPU simulation:")
        print("  python cloud_runner.py --sim your_tpu_sim.py --cores 64 --ram 512 --spot")
        print("="*60)
        return

    # Get AWS config
    key_path, key_name = get_config()

    # Update region if specified
    region = args.region

    # Select instance type
    instance_spec = select_instance_type(args.cores, args.ram)
    print(f"\nSelected instance: {instance_spec['type']}")
    print(f"  vCPUs: {instance_spec['vcpus']}, RAM: {instance_spec['ram_gb']}GB")
    print(f"  Estimated cost: {estimate_cost(instance_spec, args.spot)}")
    print("")

    # Initialize AWS clients
    ec2_client = boto3.client("ec2", region_name=region)
    ec2_resource = boto3.resource("ec2", region_name=region)

    instance = None
    try:
        # Create instance
        instance, ip = create_instance(
            ec2_client, ec2_resource,
            instance_spec["type"], key_name, args.spot, region
        )

        # Connect via SSH
        ssh = ssh_connect(ip, key_path)

        # Setup environment
        setup_meep(ssh, instance_spec["vcpus"])

        # Upload and run simulation
        upload_simulation(ssh, ip, key_path, args.sim)
        run_simulation(ssh, args.sim, instance_spec["vcpus"], args.args)

        # Download results
        download_results(ssh, ip, key_path, args.sim)

        ssh.close()

    except KeyboardInterrupt:
        print("\n\nInterrupted by user.")
    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()
    finally:
        # Clean up
        if instance and not args.keep_instance:
            terminate_instance(ec2_resource, instance)
        elif instance:
            print(f"\nInstance kept running at {ip}")
            print(f"Instance ID: {instance.id}")
            print(f"Don't forget to terminate it manually to avoid charges!")
            print(f"  aws ec2 terminate-instances --instance-ids {instance.id}")


if __name__ == "__main__":
    main()
