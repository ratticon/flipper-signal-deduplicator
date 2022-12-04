'''
///////////////////////////////////////////////////////////////////////////////

File:    signal_dedup.py
Author:  ratticon
Date:    2022-11-27

Hashes captured signal data to identify duplicates and consolidates unique
signals in specified output directory.

///////////////////////////////////////////////////////////////////////////////

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.

///////////////////////////////////////////////////////////////////////////////
'''
import os
import sys
import getopt
import glob
import shutil
import hashlib


def printSplash():
    TITLE = "signal_dedup.py - a file deduplicator for Flipper Zero signal captures"
    print()
    print('┏━' + ('━' * len(TITLE)) + '━┓')
    print('┃ ' + TITLE + ' ┃')
    print('┗━' + ('━' * len(TITLE)) + '━┛')
    print()


def query_yes_no(question, default="yes"):
    """Ask a yes/no question and return their answer.

    "question" is a string that is presented to the user.
    "default" is the presumed answer if the user just hits <Enter>.
            It must be "yes" (the default), "no" or None (meaning
            an answer is required of the user).

    The "answer" return value is True for "yes" or False for "no".
    """
    valid = {"yes": True, "y": True, "ye": True, "no": False, "n": False}
    if default is None:
        prompt = " [y/n] "
    elif default == "yes":
        prompt = " [Y/n] "
    elif default == "no":
        prompt = " [y/N] "
    else:
        raise ValueError("invalid default answer: '%s'" % default)

    while True:
        sys.stdout.write(question + prompt)
        choice = input().lower()
        if default is not None and choice == "":
            return valid[default]
        elif choice in valid:
            return valid[choice]
        else:
            sys.stdout.write("Please respond with 'yes' or 'no' " "(or 'y' or 'n').\n")


def getHash(filepath):
    '''
    Returns an MD5 hash of a given file
    '''
    md5_hash = hashlib.md5()
    with open(filepath, "rb") as f:
        # Read and update hash in chunks of 4K
        for byte_block in iter(lambda: f.read(4096), b""):
            md5_hash.update(byte_block)
        return md5_hash.hexdigest()


def getHashes(filepath, valid_extensions=['.sub'], exclude=['output']):
    """Collects hashes for all files in filepath
    Returns a dictionary of filepaths and hashes
    """
    hashes = {}
    for root, dirs, files in os.walk(filepath, topdown=True):
        dirs[:] = [d for d in dirs if d not in exclude]
        for i in files:
            f = os.path.join(root, i)
            ext = os.path.splitext(f)[1]
            if ext not in valid_extensions:
                continue
            h = getHash(f)
            # print(f"MD5 hash of {f}: {h}")
            hashes[f] = h
    return hashes


def groupDuplicateHashes(hash_dictionary={'filepath': 'hash'}):
    """Processes supplied dictionary to find duplicate hashes
    Returns dictonary of hash keys with lists of filename values. e.g:

    {
        '664b11e1cffa5af068e2cc0e22d2822c': ['file1.txt','file3.txt'],
        '9a0e7420ec65fc64f057c27d12adfe68': ['file2.txt'],
    }
    """
    # Create list of unique values
    unique_hashes = []
    for v in hash_dictionary.values():
        if v not in unique_hashes:
            unique_hashes.append(v)

    # Group files for each unique hash and add to sorted hash_dictionary
    sorted_hashes = {}
    for value in unique_hashes:
        matches = []
        for k, v in hash_dictionary.items():
            if v == value:
                matches.append(k)
        sorted_hashes[value] = matches
    return sorted_hashes


def printHashes(hash_dictionary={'hash': ['file1', 'file2']}):
    """Print all hashes in hash_dictionary and their related files, in tree
    representation. e.g:

    [1] MD5: 664b11e1cffa5af068e2cc0e22d2822c [3 matches]
     ├──file1.txt
     ├──file2.txt
     └──file3.txt

    """
    hashes_printed = 0
    for hash, filepaths in hash_dictionary.items():
        hashes_printed += 1
        print(f"[{hashes_printed}] MD5: {hash} [{len(filepaths)} matches]")
        for i, filepath in enumerate(filepaths, 1):
            prefix_char = ' ├'
            if i == len(filepaths):
                prefix_char = ' └'
            print(f"{prefix_char}─ {filepath}")
        if hashes_printed < len(hash_dictionary.items()):
            print()
    print()
    return


def copyUnique(hash_dictionary={'hash': ['file1', 'file2']}, output_path='unique_signals', overwrite=False):
    '''
    Copy a single file from each unique hash to output path
    '''
    # Ask user if it's ok to proceed
    if not overwrite and not query_yes_no(f"Copy {len(hash_dictionary)} unique signals to '{output_path}'?", "yes"):
        return False

    # Check if output folder exists
    print(f"Checking if '{output_path}' directory exists...   ", end='')
    if not os.path.exists(output_path):
        print(f"no\nCreating '{output_path}' directory... ", end='')
        try:
            os.makedirs(output_path)
        except Exception:
            print("failed. Aborting...")
            return False
        print('done')
    else:
        print("yes")

    # Check if output folder is empty
    print(f"Checking if '{output_path}' directory is empty... ", end='')
    if len(os.listdir(output_path)) > 0:
        print("no")
        # Ask for confirmation to clear it if not
        if not overwrite and not query_yes_no(f" [!] WARNING: OK to delete the contents of '{output_path}'?", "yes"):
            print("Aborting...")
            return False
        # Clear contents of output folder
        print(f"\nDeleting the contents of '{output_path}'...")
        output_contents = glob.glob(output_path + os.sep + '*')
        for f in output_contents:
            os.remove(f)
            print(f" [!] DESTROYED '{f}'")
    else:
        print("yes")

    # Copy unique files to output folder
    print("\nCopying 1 file per unique signal...")
    files_copied = 0
    total_files = 0
    for hash, filepaths in hash_dictionary.items():
        total_files += len(filepaths)
        files_copied += 1
        src = filepaths[0]
        src_basename = os.path.basename(src)
        dst = output_path + os.sep + src_basename
        shutil.copy(src, dst)
        prefix_character = '├'
        end = ''
        if files_copied == len(hash_dictionary.items()):
            prefix_character = '└'
            end = '\n'
        print(f"{prefix_character}─[{files_copied}] MD5: {hash} ─> Copied {src_basename}{end}")

    # Return True or False for success
    print(f"Done! (Reduced {total_files} files to {files_copied})")
    return True


def main(argv):
    overwrite = False
    input_path = '.'
    output_path = 'output'

    printSplash()

    # Process launch arguments
    try:
        opts, args = getopt.getopt(argv, "yi:o:", ["yes", "input_path=", "output_path="])
    except getopt.GetoptError:
        print('Syntax error!\nUsage: signal_dedup.py -i <input path> -o <output path>')
        sys.exit(2)
    for opt, arg in opts:
        if opt in ("-y", "--yes"):
            print('[!] WARNING: -y/--yes specified!\n    Data will be destroyed/overwritten without prompting!\n')
            overwrite = True
        elif opt in ("-i", "--input_path"):
            input_path = str(arg).strip()
        elif opt in ("-o", "--output_path"):
            output_path = str(arg).strip()
            # Prevent bare output path
            if output_path in ('.', '/'):
                print(f'[!] Outputting to {output_path} is dangerous, changing to \'output\'!\n')
                output_path = 'output'

    # MD5 hash all .sub files at input_path
    hash_dictionary = getHashes(input_path, valid_extensions=['.sub'], exclude=['output', output_path])

    # Quit early if no .sub files found
    if len(hash_dictionary) < 1:
        print(f'[!] No signals found in \'{input_path}\'. Exiting...')
        sys.exit(0)

    # Process all collected hashes and group by unique
    hash_dictionary = groupDuplicateHashes(hash_dictionary)
    printHashes(hash_dictionary)

    # Copy one file per unique hash to output_path
    copyUnique(hash_dictionary, output_path, overwrite)


if __name__ == "__main__":
    main(sys.argv[1:])
