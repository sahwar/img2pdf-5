#!/usr/bin/python3

from os.path import exists, isfile, join, expanduser, basename, isdir, dirname
from shutil import copyfile, rmtree
import sys
from reportlab import platypus
from reportlab.platypus import Paragraph
from reportlab.lib.units import inch
from reportlab.lib.styles import getSampleStyleSheet
from PIL import Image
from tempfile import mkdtemp
from re import search
from os import remove, listdir
import argparse

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
SCALE_SPACED_A4 = 1.9
SCALE_SPACED = SCALE_SPACED_A4
#white spaces to put before and after each image (inches)
SPACE_BEFORE_IMAGE1 = 0.2 #inch
SPACE_AFTER_IMAGE1 = 0.2 #inch
SPACE_BEFORE_IMAGE2 = 0.4 #inch
SPACE_AFTER_IMAGE2 = 0.2 #inch

DESC_FILE_NAME = 'description.txt'
PATH_DESC_MAP = {}
DESC_DONE = {}
styles = getSampleStyleSheet()
style_heading1 = styles['Heading1']

class PdfCreator:
    def __init__(self, src_images_path, dest_pdf_path = None, scale = SCALE_FULL,
                 space_before_image1 = SPACE_BEFORE_IMAGE1, 
                 space_after_image1 = SPACE_AFTER_IMAGE1,
                 space_before_image2 = SPACE_BEFORE_IMAGE2, 
                 space_after_image2 = SPACE_AFTER_IMAGE2):
        if not src_images_path:
            print('No input images specified...exiting')
            sys.exit(1)

        self.__imagePaths = src_images_path
        self.__tempDir = mkdtemp()
        self.__pdfPath = join(expanduser('~'), "workout.pdf") if not dest_pdf_path else dest_pdf_path
        self.__scale = scale
        self.__space_before_image1 = space_before_image1
        self.__space_after_image1 = space_after_image1
        self.__space_before_image2 = space_before_image2
        self.__space_after_image2 = space_after_image2
        
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
    def dest_pdf_path(self):
        return self.__pdfPath

    def __filterImgFiles(self):
        paths = list(filter(self.__isImageFile, self.__imagePaths))
        if not len(paths):
            print("Error: there are no files for processing!")
            return None
        return paths
    #removed because copying to temp files not really required
#         tmpPaths = []
#         for src in paths:
#             dst = join(self.__tempDir, basename(src))
#             copyfile(src, dst)
#             tmpPaths.append(dst)
#         return tmpPaths

  
    #internal function to put 2 images per A4 sized PDF page in portrait mode
    def __createPdfFromImages(self, src_images_path):
        doc = platypus.SimpleDocTemplate(self.__pdfPath)
        doc.leftMargin = 0
        doc.bottomMargin = 0
        doc.rightMargin = 0
        doc.topMargin = 0

        pageWidth = PAGE_WIDTH_MM * self.__scale

        story = []
        hasStory = False
        i = 1;
        for image_file in src_images_path:
            try:
                pilImg = Image.open(image_file)
                print('Adding ' + basename(image_file) + ' to pdf document...')
            except Exception:
                print('Cannot access a file: ' + image_file)
                continue

            imageWidth = pilImg.size[0]
            print('imageWidth:', imageWidth)
            imageHeight = pilImg.size[1]
            print('imageHeight:', imageHeight)
 
#           desc = 'Paragraph number
            desc_file = join(dirname(image_file), DESC_FILE_NAME)
            print('desc_file:', desc_file)
            desc = None
            if exists(desc_file):
                desc = read_desc(desc_file);
            print('desc:', desc)
            if desc is not None and not DESC_DONE.get(desc_file, False):  
                para = Paragraph(desc, style_heading1)  
                story.append(para)
                DESC_DONE[desc_file] = True
            
            #put different spaces before first and second images on every page
            if not i % 2:
                story.append(platypus.Spacer(1, self.__space_before_image1 * inch))
            else:
                story.append(platypus.Spacer(1, self.__space_before_image2 * inch))
                
            repImg = platypus.Image(image_file, pageWidth, 
                            pageWidth * (imageHeight/imageWidth))
            story.append(repImg)
            #put some space after every image
            if not i % 2:
                story.append(platypus.Spacer(1, self.__space_after_image1 * inch))
            else:
                story.append(platypus.Spacer(1, self.__space_after_image2 * inch))

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

    def createPdf(self):
        src_images_path = self.__filterImgFiles()
        if not src_images_path:
            return False
        result = self.__createPdfFromImages(src_images_path)
        rmtree(self.__tempDir)
        return result

    def __isImageFile(self, p):
        return exists(p) and isfile(p) and search(r'\.jpg$|\.bmp$|\.tiff$|\.png$|\.gif$|\.jpeg$', p) != None

########################################################################

def recursiveSearch(p, fps):
    def enumFilesInDir():
        _files = listdir(p)
        desc_found = False
        for i in range(0, len(_files)):
            file = _files[i]
            _files[i] = join(p, file)
            if not desc_found and exists(file) and isfile(file) and basename(file) == DESC_FILE_NAME:
                PATH_DESC_MAP[p] = _files[i]
                desc_found = True
                            
        return _files
    files = enumFilesInDir()
    for f in files:
        assert exists(f), "File or directory not found: " + f
        if isdir(f):
            recursiveSearch(f, fps)
        elif isfile(f):
            fps.append(f)

# def recurse_create_pdf(p, fps):
    

def parseArgs():
    parser = argparse.ArgumentParser(description="img2pdf.py is very simple python script to convert "
                                                 "image files to a single pdf file (A4 paper size)")
    parser.add_argument("-d", "--directories",
                        help="search image files in specified directories (recursive search only)", type=str, nargs="+")
#     parser.add_argument("-f", "--files",
#                         help="image file names", type=str, nargs="+")
#     parser.add_argument("--printer",
#                         help="if this option is enabled, "
#                              "script createPdf the pdf file and print it on a default printer", action="store_true")
    parser.add_argument("--out",
                        help="Full path of the PDF file (~/workout.pdf is default) ", type=str)
    args = parser.parse_args()

    src_images_path = []
    if args.directories:
        for src_dir in args.directories:
            recursiveSearch(src_dir, src_images_path)
#     if args.files:
#         for file in args.files:
#             assert exists(file) and isfile(file), "File or directory not found: " + file
#             src_images_path.append(file)
    return src_images_path, args.out

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
    
    src_images_path, dest_pdf_path = parseArgs()
    pdfCreator = PdfCreator(src_images_path, dest_pdf_path, SCALE_FULL, 
                            SPACE_BEFORE_IMAGE1, SPACE_AFTER_IMAGE1,
                            SPACE_BEFORE_IMAGE2, SPACE_AFTER_IMAGE2)
    pdfCreator.createPdf()
#     if isPrint:
#         subprocess.call(["lpr", pdfCreator.dest_pdf_path])
