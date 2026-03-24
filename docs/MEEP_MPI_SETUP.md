# Meep MPI Setup Reference

The default `conda install pymeep` installs the **nompi** build, which is **single-threaded**.
Setting `OMP_NUM_THREADS` does **nothing** with the nompi build. You must install the MPI version.

## Check if your Meep is parallel

```bash
conda list pymeep
# Look for "mpi_mpich" in the build string
# GOOD: pymeep  1.31.0  mpi_mpich_py312h639cf41_0  conda-forge
# BAD:  pymeep  1.31.0  nompi_py312...              conda-forge
```

## Install MPI-enabled Meep

```bash
# Fresh environment (Python 3.12 — 3.13 has compatibility issues)
conda create -n meep_env python=3.12 -y
conda activate meep_env
conda install -c conda-forge "pymeep=*=mpi_mpich*" mpi4py mpich matplotlib numpy scipy h5py

# Or fix an existing nompi install
conda install -c conda-forge "pymeep=*=mpi_mpich*" mpi4py mpich --force-reinstall
```

## Run with MPI

```bash
# WRONG — runs single-threaded even with MPI build
python simulation.py

# CORRECT — uses all cores
mpirun -np $(nproc) python simulation.py

# Or specify core count
mpirun -np 32 python simulation.py
```

## MPI boilerplate for Python scripts

```python
import meep as mp

# MPI support
try:
    from mpi4py import MPI
    RANK = MPI.COMM_WORLD.Get_rank()
    SIZE = MPI.COMM_WORLD.Get_size()
    IS_PARALLEL = SIZE > 1
except ImportError:
    RANK = 0
    SIZE = 1
    IS_PARALLEL = False

def print_master(msg):
    """Only print from rank 0 to avoid duplicate output."""
    if RANK == 0:
        print(msg)
```

## Verify MPI is working

```python
import meep as mp
print(f"Meep version: {mp.__version__}")
print(f"MPI enabled: {mp.with_mpi()}")  # Must be True
```

## Scaling notes

- 64 cores gives ~1.5-1.7x speedup over 32 (not 2x) due to MPI communication overhead
- Sweet spot: 32-64 cores for large simulations
- Beyond 128 cores: diminishing returns
