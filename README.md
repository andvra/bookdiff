# Introduction

Use stylometry to decide author of a given book.
First time you run the project, all authors from Project Gutenberg will be scraped. Then _n_ authors are selected and their corpus is downloaded. A few books are extracted from the corpus to use for validation. Then the algorithms perform their magic on the remaining corpus, using these steps:

1. Merge all raw text
2. Find the x most frequent features (words)
3. Find the mean ![img](http://latex.codecogs.com/svg.latex?%5Cmu) and standard deviation ![img](http://latex.codecogs.com/svg.latex?%5Csigma) for each feature
4. For each feature and subcorpus (all books written by an author), calculate the z-value:  
   &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;![img](http://latex.codecogs.com/svg.latex?Z_{i}%3D\frac{C_{i}-\mu_{i}}{\sigma_{i}})
5. For each book in the validation set, compare its z-values with each of the subcorpus. The author of the subcorpus that gives the lowest delta is the most likely to have written the given book

## Setup

1. Download the books in txt format, for instance using the torrent files [here](https://www.gutenberg.org/wiki/Gutenberg:The_CD_and_DVD_Project#Downloading_Via_BitTorrent)
2. Create a file config.json in the root folder with the following structure:

```json
{
  "scp": {
    "ip": "<IP>",
    "port": PORT,
    "username": "USERNAME",
    "password": "PASSWORD",
    "path": "/path/to/remote/txt/folder/"
  },
  "local_book_lib": "/path/to/local/txt/folder/",
  "min_books": 10,
  "max_books": 10000,
  "number_of_authors": 5
}
```

I had the Gutenberg text files downloaded on a remote computer so used SCP for that. If you prefer having the textbooks locally, skip the SCP section of the JSON and add your local path to local_book_lib instead.

## References

- Source for raw text books is [Project Gutenberg](https://www.gutenberg.org/)
- Introduction to stylometry by [François Dominic Laramée](https://programminghistorian.org/en/lessons/introduction-to-stylometry-with-python#third-stylometric-test-john-burrows-delta-method-advanced)
