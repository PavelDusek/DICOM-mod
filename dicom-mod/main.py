# coding: utf-8
import pydicom
import numpy as np
import argparse
import os

from pathlib import Path
from PIL import Image
from icecream import ic
from rich import print
from functools import wraps

parser = argparse.ArgumentParser(
    prog="dicom-mod",
    description="A script to modify DICOM files.",
    epilog="See https://github.com/PavelDusek/DICOM-mod",
)
parser.add_argument("-i", "--input", type=str, help="input directory")
parser.add_argument("-o", "--output", type=str, help="output directory")
parser.add_argument("-s", "--show", action="store_true", default=False, help="show dicom images")
parser.add_argument("-j", "--jpg", action="store_true", default=False, help="Convert dicom to jpg.")
parser.add_argument("-n", "--info", action="store_true", default=True, help="Print information about the image.")
parser.add_argument("-v", "--verbose", action="store_true", default=False, help="Verbose output.")

#TODO institution
# (0008,0080) Institution Name                    LO: 'Univerzita Karlova v Praze'
#
#TODO check for pixel data
# (7FE0,0010) Pixel Data                          OW: Array of 3686400 elements
#

############
# Transfer #
############
parser.add_argument("-t", "--transfer", action="store_true", default=False, help="Transfer part of the dicom image to another x,y value specified by --source and --destination.")
parser.add_argument("-u", "--source", type=str, default="950,0,150,65", help="Part of the image to be transfered, argument for --transfer. Format: x,y,width,height. x,y is the top left corner of the rectangle with width and height.")
parser.add_argument("-e", "--debug", action="store_true", default=False, help="If exception raised, run Python debugger.")
parser.add_argument("-d", "--destination", type=str, default="10,0", help="color as (r,g,b) for --fill.")

parser.add_argument("-t2", "--transfer2", action="store_true", default=False, help="Transfer part of the dicom image to another x,y value specified by --source and --destination.")
parser.add_argument("-u2", "--source2", type=str, default="780,35,310,30", help="Part of the image to be transfered, argument for --transfer. Format: x,y,width,height. x,y is the top left corner of the rectangle with width and height.")
parser.add_argument("-d2", "--destination2", type=str, default="150,35", help="color as (r,g,b) for --fill.")

########
# Fill #
########
parser.add_argument("-f", "--fill", action="store_true", default=False, help="Fill part of the dicom images with color specified with --color in the rectangle specified by --rect. It could be use to anonymize images.")
parser.add_argument("-c", "--color", type=str, default="23,34,61", help="color as (r,g,b) for --fill.")
parser.add_argument("-r", "--rect", type=str, default="10,0,150,65", help="rectangle as x,y,width,height, x,y is the top left corner of the rectangle for --fill")

parser.add_argument("-f2", "--fill2", action="store_true", default=False, help="Fill another part of the dicom images with color specified with --color in the rectangle specified by --rect. It could be use to anonymize images.")
parser.add_argument("-c2", "--color2", type=str, default="23,34,61", help="color as (r,g,b) for --fill2.")
parser.add_argument("-r2", "--rect2", type=str, default="150,30,300,35", help="rectangle as x,y,width,height, x,y is the top left corner of the rectangle for --fill2.")

args = parser.parse_args()

#############
# Functions #
#############
def debug_verbose(debug:bool = False, verbose: bool = False):
    """Function decorator to show debug info in case of failure of a function and verbose info in case of verbose arguments."""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            result = None
            if debug:
                print(f"Running {func}.")
            if verbose:
                ic(func)
                ic(args)
                ic(kwargs)
            try:
                result = func(*args, **kwargs)
                return result
            except AttributeError as e:
                print(e)
                if debug:
                    breakpoint()
            return result
        if debug:
            print(f"End of {func}.")
        return wrapper
    return decorator

@debug_verbose(args.debug, args.verbose)
def show_image(array: np.array, zoom = False) -> str:
    """ Shows the actual image in an numpy array on the display."""
    image = Image.fromarray(array)
    img = image.convert('RGB')
    img.show()
    print("[blue]Enter[/blue] to continue, [red]Q[/red] to end.")
    return input("Proceed?")

@debug_verbose(args.debug, args.verbose)
def fill_image(array: np.array, rectangle: str, color: str) -> np.array:
    """ Fills part of the image with a rectangle with specified color."""
    x, y, width, height = rectangle.split(",")
    r, g, b = color.split(",")
    x, y, width, height, r, g, b = int(x), int(y), int(width), int(height), int(r), int(g), int(b)
    array[ y:y+height, x:x+width ] = [r, g, b]
    return array

@debug_verbose(args.debug, args.verbose)
def transfer_image(array: np.array, destination: str, source: str) -> np.array:
    """ Transfers part of the image to a different part of the image as a copy."""
    source_x, source_y, width, height = source.split(",")
    dest_x, dest_y = destination.split(",")
    source_x, source_y, width, height, dest_x, dest_y = int(source_x), int(source_y), int(width), int(height), int(dest_x), int(dest_y)
    array[ dest_y : dest_y+height, dest_x : dest_x+width ] = array[ source_y : source_y+height, source_x : source_x+width ]
    return array

@debug_verbose(args.debug, args.verbose)
def get_image(dataset: pydicom.dataset.FileDataset) -> np.array:
    ic(dataset.pixel_array)
    return dataset.pixel_array

@debug_verbose(args.debug, args.verbose)
def save_jpg(image: np.array) -> None:
    pil_image = Image.fromarray(image)
    pil_image.save(out_path)

def main() -> bool:
    in_dir, out_dir = None, None
    if args.input:
        in_dir  = Path(args.input)
    else:
        print("[red]No input directory specified.[/red]")
        return False
    if args.output:
        out_dir = Path(args.output)
    else:
        print("[red]No output directory specified.[/red]")

    for path in in_dir.iterdir():
        print(f"Parsing file [blue]{path}[/blue].")
        dataset = pydicom.dcmread(in_dir / path)
        image = get_image(dataset)

        if args.info:
            print(f"Shape of image [green]{image.shape}[/green].")
        if args.transfer:
            image = transfer_image(array = image, destination = args.destination, source = args.source)
        if args.transfer2:
            image = transfer_image(array = image, destination = args.destination2, source = args.source2)
        if args.fill:
            image = fill_image(array = image, rectangle = args.rect, color = args.color)
        if args.fill2:
            image = fill_image(array = image, rectangle = args.rect2, color = args.color2)

        if args.show:
            print(f"Showing [green]{path.name}[/green].")
            command = show_image(image)
            if command.strip().lower() in ["q", "quit", "e", "exit"]:
                return False

        if args.jpg and out_dir:
            jpg_name = f"{path.name}.jpg"
            if not out_dir.is_dir():
                os.makedirs(out_dir)
            out_path = out_dir / Path(jpg_name)
            print(f"Saving image to [green]{out_path}[/green].")

        if out_dir:
            if not out_dir.is_dir():
                os.makedirs(out_dir)
            out_path = out_dir / path.name
            dataset.PixelData = image.tobytes()
            print(f"Saving dicom file to [red]{out_path}[/red].")
            dataset.save_as(out_path, enforce_file_format = True)
    return True

if __name__ == "__main__":
    main()
