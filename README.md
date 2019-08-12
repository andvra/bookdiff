# Introduction

Use stylometry to decide author of a given book.
First time you run the project, all authors from Project Gutenberg will be scraped. Then _n_ authors are selected and their corpus is downloaded. A few books are extracted from the corpus to use for validation. Then the algorithms perform their magic on the remaining corups, using these steps:

1. Merge all raw text
2. Find the x most frequent features (words)
3. Find the mean u and standard deviation sigma for each feature
4. For each feature and subcorpus (all books written by an author), calculate the z-value:
   ![img](http://latex.codecogs.com/svg.latex?Z_{i}%3D\frac{C_{i}-\mu_{i}}{\sigma_{i}})
5. For each book in the validation set, compare its z-values with each of the authors. The author with the smallest delta is the most likely author

Source for raw text books is [Project Gutenberg](https://www.gutenberg.org/)
