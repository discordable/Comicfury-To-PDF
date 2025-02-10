
import tkinter as tk
from tkinter import *
from tkinter.ttk import *
from tkinter import Text
from tkinter import Label
from tkinter import filedialog

import sys
import os
from os import walk
import urllib.request, json
import requests
from PIL import Image
import pypdf

def download_pages(comic_name, comic_directory, start):
    # automatically find the number of pages
    profile_url = "https://comicfury.com/comicprofile.php?url=" + comic_name
    comic_url = "https://" + comic_name + ".thecomicseries.com/comics/"
    profile_response = requests.get(profile_url)
    profile_response.raise_for_status()  # raises exception when not a 2xx response
    start_index = profile_response.text.find("Number of comics:") + 44 # hardcoded to find number of pages
    end_index = profile_response.text.find("<", start_index)
    num_pages_substring = profile_response.text[start_index : end_index]
    number_of_pages = int(num_pages_substring)

    # download all pages, starting at a specifed page
    i = start
    while i < number_of_pages:
        url = comic_url + str(i + 1)
        response = requests.get(url)
        response.raise_for_status()  # raises exception when not a 2xx response
        start_index = response.text.find("og:image") + 19 # hardcoded to find image link
        end_index = response.text.find("\"", start_index)
        image_link = response.text[start_index : end_index]
        urllib.request.urlretrieve(image_link, comic_directory + comic_name + "_" + str(i + 1) + image_link[image_link.find(".", len(image_link) - 5):])
        update_progress_bar(i + 1, number_of_pages)
        i += 1

def images_to_pdf(comic_name, comic_directory, output_pdf):
    # convert non-compatable images to .jpg
    for f in os.listdir(comic_directory): 
        if not f.endswith('.jpg') and not f.endswith('.jpeg'): 
            Image.open(comic_directory + f).convert('RGB').save(comic_directory + f[:f.find('.png')] + '.jpg')
    for f in os.listdir(comic_directory): 
        if not f.endswith('.jpg') and not f.endswith('.jpeg'):
            os.remove(comic_directory + f)

    # convert images to pdf
    image_names = next(walk(comic_directory), (None, None, []))[2]
    sort_key = lambda s: (len(s), s) # sorts based on alphabet and length, allowing for 10 to come after 9
    image_names.sort(key=sort_key)
    images = [Image.open(comic_directory + f) for f in image_names]
    images[0].save(output_pdf, 'PDF', resolution=100.0, save_all=True, append_images=images[1:])

    # clean up
    for f in image_names:
        os.remove(comic_directory + f)

def get_num_pages(pdf):
    with open(pdf, 'rb') as pdf_file:
        reader = pypdf.PdfReader(pdf_file)
        return len(reader.pages)

def get_comic_name(entry):
    if 'thecomicseries.com' in entry:
        return entry[8 : entry.find('.thecomicseries.com')]
    elif 'comicfury.com' in entry:
        return entry[entry.find('url=') + 4:]
    elif 'webcomic.ws' in entry:
        return entry[8 : entry.find('.webcomic.ws')]
    elif 'the-comic.org' in entry:
        return entry[8 : entry.find('.the-comic.org')]
    elif 'cfw.me' in entry:
        return entry[8 : entry.find('.cfw.me')]
    else:
        return entry

def merge_pdfs(pdf1, pdf2):
    merger = pypdf.PdfWriter()
    merger.append(pdf1)
    merger.append(pdf2)
    merger.write(pdf1)
    merger.close()
    os.remove(pdf2)

def update_progress_bar(current_page, total_pages):
    pbar['value'] = (current_page / total_pages) * 100
    root.update_idletasks()

def create_pdf():
    try:
        pbar.pack(padx=20, pady=10)
        comic_name = get_comic_name(entry.get())
        # create new directory to store downloaded images
        comic_directory = comic_name + "\\"
        if not os.path.exists(comic_directory):
            os.makedirs(comic_directory)
        first_message.config(text='Downloading pages. This may take a while...')
        download_pages(comic_name, comic_directory, 0)
        first_message.config(text='Creating pdf...')
        images_to_pdf(comic_name, comic_directory, comic_name + '.pdf')
        os.rmdir(comic_directory)
        first_message.config(text='Success! You can find your new pdf in the directory this is running from.')
    except:
        print('Something went wrong. Stopping...')
        first_message.config(text='Sorry, something went wrong...')

def update_pdf():
    try:
        pbar.pack(padx=20, pady=10)
        old_pdf = filedialog.askopenfilename()
        comic_name = old_pdf[old_pdf.rfind('/') + 1 : len(old_pdf) - 4]
        if 'That webcomic was not found!' in requests.get('https://comicfury.com/comicprofile.php?url=' + comic_name).text:
            comic_name = get_comic_name(entry.get())
        # create new directory to store downloaded images
        comic_directory = comic_name + "\\"
        if not os.path.exists(comic_directory):
            os.makedirs(comic_directory)
        second_message.config(text='Downloading pages. This may take a while...')
        download_pages(comic_name, comic_directory, get_num_pages(old_pdf))
        second_message.config(text='Updating pdf...')
        images_to_pdf(comic_name, comic_directory, comic_name + '_update.pdf')
        merge_pdfs(old_pdf, comic_name + '_update.pdf')
        os.rmdir(comic_directory)
        second_message.config(text='Success! Your pdf has been updated.')
    except:
        print('Something went wrong. Stopping...')
        second_message.config(text='Sorry, something went wrong...')

# main window
root = tk.Tk()
root.title("Comic Downloader")

# first message
first_message = Label(root, padx=20, pady=10, text='To download a comic, enter a comic name or link, then click the button.\n (remember this only works with comicfury)')
first_message.pack()

# user entry field
entry = tk.Entry(root, width=30)
entry.insert(tk.END, "https://example.thecomicseries.com")
entry.pack(padx=20, pady=10)

# create pdf button
b1 = tk.Button(root, text="Create pdf", command=create_pdf)
b1.pack(padx=20, pady=10)

# second message
second_message = Label(root, padx=20, pady=10, text='You can also update an existing pdf with new pages using this button:\n(please still enter a comic name or link)')
second_message.pack()

# update pdf button
b2 = tk.Button(root, text="Update pdf", command=update_pdf)
b2.pack(padx=20, pady=10)

# download progress bar
pbar = Progressbar(root, orient=tk.HORIZONTAL, length=500)

# execute main window
if __name__ == '__main__':
    root.mainloop()

