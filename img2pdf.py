#!/usr/bin/python3

from os.path import exists, isfile, join, expanduser, basename, isdir
from shutil import copyfile, rmtree
import sys
from reportlab import platypus
from reportlab.lib.units import inch
from PIL import Image
from tempfile import mkdtemp
from re import search
from os import remove, listdir
import argparse
import subprocess

A4_WIDTH_MM = 210 #A4 width (mm)
A4_HEIGHT_MM = 297 #A4 height (mm)

#current program is set to put 2 images per A4 size page in portrait mode, 
#change below 2 globals to other values like Letter size etc 
PAGE_WIDTH_MM = A4_WIDTH_MM
PAGE_HEIGHT_MM = A4_HEIGHT_MM

#SCALE_* globals denote a number found by trial by which any sized image
#be will be fit into the page (width/height variables set above)
#occupy most of page leaving little white space around images. Modify
#for sizes other than A4 (also modify PAGE_* globals above for non-A4)
SCALE_FULL_A4 = 2.3
SCALE_FULL = SCALE_FULL_A4
#leave some white space around images
SCALE_SPACED_A4 = 2.0
SCALE_SPACED = SCALE_SPACED_A4
#white spaces to put before and after each image (inches)
SPACE_BEFORE_IMAGE = 0.45 #inch
SPACE_AFTER_IMAGE = 0.45 #inch

class PdfCreator:
    def __init__(self, imagePaths, pdfPath = None, scale = SCALE_FULL,
                 space_before_image = SPACE_BEFORE_IMAGE, 
                 space_after_image = SPACE_AFTER_IMAGE):
        if not imagePaths:
            print('No input images specified...exiting')
            sys.exit(1)

        self.__imagePaths = imagePaths
        self.__tempDir = mkdtemp()
        self.__pdfPath = join(expanduser('~'), "workout.pdf") if not pdfPath else pdfPath
        self.__scale = scale
        self.__space_before_image = space_before_image
        self.__space_after_image = space_after_image
        self.__desc_file = 'desc.txt'
        
    @property
    def tempDir(self):
        return self.__tempDir

    @tempDir.setter
    def tempDir(self, tempDir):
        if not isinstance(tempDir, str):
            raise TypeError
        import sys
        assert exists(tempDir), "The temp directory path must be valid"
        self.__tempDir = tempDir

    @property
    def pdfPath(self):
        return self.__pdfPath

    def __prepare(self):
        paths = list(filter(self.__condition, self.__imagePaths))
        if not len(paths):
            print("Error: there are no files for processing!")
            return None
        tmpPaths = []
        for src in paths:
            dst = join(self.__tempDir, basename(src))
            copyfile(src, dst)
            tmpPaths.append(dst)
        return tmpPaths

    #internal function to put 2 images per A4 sized PDF page in portrait mode
    def __convert(self, imagePaths):
        doc = platypus.SimpleDocTemplate(self.__pdfPath)
        doc.leftMargin = 0
        doc.bottomMargin = 0
        doc.rightMargin = 0
        doc.topMargin = 0

        pageWidth = PAGE_WIDTH_MM * self.__scale

        story = []
        hasStory = False
        i = 1;
        for p in imagePaths:
            try:
                pilImg = Image.open(p)
                print('Adding ' + basename(p) + ' to pdf document...')
            except Exception:
                print('Cannot access a file: ' + p)
                continue

            imageWidth = pilImg.size[0]
            print('imageWidth:', imageWidth)
            imageHeight = pilImg.size[1]
            print('imageHeight:', imageHeight)
            
            #put some space before first image on every page
            if i % 2:
                story.append(platypus.Spacer(1, self.__space_before_image * inch))
            repImg = platypus.Image(p, pageWidth, 
                            pageWidth * (imageHeight/imageWidth))
            story.append(repImg)
            #put some space after every image
            story.append(platypus.Spacer(1, self.__space_after_image * inch))

            #break page after every 2 images
            if not i % 2:
                story.append(platypus.PageBreak())
            i += 1                
            print('OK')
            hasStory = True
        doc.build(story)
        if hasStory:
            print("Pdf file was created successfully")
        else:
            print("Pdf file was not created")
            if exists(self.__pdfPath):
                remove(self.__pdfPath)
        return hasStory

    def create(self):
        imagePaths = self.__prepare()
        if not imagePaths:
            return False
        result = self.__convert(imagePaths)
        rmtree(self.__tempDir)
        return result

    def __condition(self, p):
        return exists(p) and isfile(p) and search(r'\.jpg$|\.bmp$|\.tiff$|\.png$|\.gif$|\.jpeg$', p) != None

########################################################################

def recursiveSearch(p, fps):
    def enumFilesInDir():
        _files = listdir(p)
        for i in range(0, len(_files)):
            _files[i] = join(p, _files[i])
        return _files
    files = enumFilesInDir()
    for f in files:
        assert exists(f), "File or directory not found: " + f
        if isdir(f):
            recursiveSearch(f, fps)
        elif isfile(f):
            fps.append(f)


def parseArgs():
    parser = argparse.ArgumentParser(description="img2pdf.py is very simple python script to convert "
                                                 "image files to a single pdf file (A4 paper size)")
    parser.add_argument("-d", "--directories",
                        help="search image files in specified directories (recursive search only)", type=str, nargs="+")
    parser.add_argument("-f", "--files",
                        help="image file names", type=str, nargs="+")
    parser.add_argument("--printer",
                        help="if this option is enabled, "
                             "script create the pdf file and print it on a default printer", action="store_true")
    parser.add_argument("--out",
                        help="Full path of the PDF file (~/workout.pdf is default) ", type=str)
    args = parser.parse_args()

    filePaths = []
    if args.directories:
        for dir in args.directories:
            recursiveSearch(dir, filePaths)
    if args.files:
        for file in args.files:
            assert exists(file) and isfile(file), "File or directory not found: " + file
            filePaths.append(file)
    return args.printer, filePaths, args.out

########################################################################
#read and return text from description file in each images folder.  Description
#text will most likely be a single line of text which describes the images in that
#folder 
def read_desc(file_name):
    desc = None
    with open(file_name, 'r') as myfile:
        desc = myfile.read()
    return desc
    
if __name__ == "__main__":
    
    isPrint, filePaths, pdfPath = parseArgs()
    pdfCreator = PdfCreator(filePaths, pdfPath, SCALE_FULL, SPACE_BEFORE_IMAGE,
                            SPACE_AFTER_IMAGE)
    pdfCreator.create()
    if isPrint:
        subprocess.call(["lpr", pdfCreator.pdfPath])
