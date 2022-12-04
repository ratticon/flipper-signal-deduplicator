# flipper-signal-deduplicator

MD5 hashes captured signal data (.sub files) to identify duplicates, then copies only unique signals to `./output` directory.

Copy `signal_dedup.py` to the folder containing your `.sub` files and run it, or vice versa.   
Unique `.sub` files will be copied to the `output` directory by default.

![Screenshot of signal_dedup.py in action](sample.png)

Written with Python 3.9.13 using only standard libraries. ♡

## Usage:
To process `.sub` files within the same path as `signal_dedup.py` and copy unique signals to subdirectory `output`:
```
python signal_dedup.py
```
To specify input and/or output paths:
```
python signal_dedup.py -i <input path> -o <output path>
```

## Valid Options:

| Short | Long            | Argument(s)     | Description                      | Example                         |
| ----- | --------------  | --------------- | -------------------------------- | ------------------------------- |
| `-i`  | `--input_path`  | input filepath  | Path to search for `.sub` files  | `-i /mnt/sd_card/subghz`        |
| `-o`  | `--output_path` | output filepath | Path to copy unique files to     | `-o /mnt/sd_card/subghz/unique` |
| `-y`  | `--yes`         | none            | **Dangerous**: Answer yes to all questions. Will delete / overwrite files without asking. | `-y`                              |
