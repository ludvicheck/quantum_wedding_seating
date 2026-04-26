# Wedding Seating Optimization with Classical and Quantum Approaches

This repository contains code for solving a constrained wedding seating problem at a single table with 18 seats.

The problem combines:
- pairwise guest preferences from -5 to 5
- hard constraints for couples and special seating rules
- a rectangular table geometry
- both classical and quantum-oriented optimization approaches

## Problem description

Each guest must be assigned to exactly one seat, and each seat must contain exactly one guest.

The objective is to maximize total seating compatibility based on:
- positive preferences for guests who should sit close together
- negative preferences for guests who should sit far apart
- special bonuses or constraints for couples
- table-specific geometry (same-side neighbors, opposite seats, middle seats, edge seats)

The current instance uses:
- 18 guests
- 18 seats
- a rectangular table with seats 1..9 on one side and 10..18 on the other side

## Implemented approaches

### Classical solver
A CP-SAT model using Google OR-Tools.

### Quantum-oriented solver
A QUBO/BQM formulation intended for D-Wave Ocean / Advantage systems.

## Repository structure

- `classical/` — OR-Tools implementation
- `dwave/` — D-Wave QUBO implementation
- `data/` — example seating instance
- `examples/` — sample outputs

## Installation

```bash
pip install -r requirements.txt