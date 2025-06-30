#!/bin/bash

input_dir="Inputs"
output_dir="outputs"

mkdir -p "$output_dir"

for filename in "$input_dir"/*; do
    basefile=$(basename "$filename")
    python3 main_multiframe.py --input "$input_dir/$basefile" --output "$output_dir/$basefile" --consider_shear
done
