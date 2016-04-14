import glob
import sys
import numpy as np
from argparse import ArgumentParser
from bs4 import BeautifulSoup

DEBUG = False

class Page(object):

  def __init__(self, filename, links_weight=None):
    self._filename = filename
    self._base = 0
    self._score = 0
    self._newscore = 0
    if links_weight is None:
      links_weight = {}
      self._links_weight = links_weight
  # called when doing comparison such as obj1 < obj2
  def __cmp__(self, other):
    if hasattr(other, '_score'):
      return self._score.__cmp__(other._score)

  # BeautifulSoup's get_text() will return incorrect results
  def wordcount(self):
    with open (self._filename) as f:
      contents = f.read()
      count = len(contents.split())
      f.close()
      return count

  # calculate the weight of specific link in a page
  def get_link_weight(self, link):
    score = 1
    # check if link is in the scope of <H1>, <H2>, <H3>, <H4>, <em> or <b>
    scopes = ['H1', 'H2', 'H3', 'H4', 'em', 'b']
    for parent in link.parents:
      if parent == None:
        continue
      if parent.name in scopes:
        score += 1
    # print link, score
    return score


  def calc_links_weight(self, links):
    '''
    return: normalized weight of links in dictionary format
    [link1:weight, link2:weight]
    '''

    links_weight = {}
    normailized_weight = {}
    # f = open(self._filename, 'r')
    # contents = f.read()
    #
    # soup = BeautifulSoup(contents, "html.parser")
    # links = soup.find_all('a')
    #
    # if len(links) != 0:
    for link in links:
      name = link.get('href')
      if name in links_weight:
        links_weight[name] = links_weight[name]+ self.get_link_weight(link)
      else:
        links_weight[name] = self.get_link_weight(link)

    # print "non-normalized links weight is: \n %s" % links_weight
    sum = 0
    for key in links_weight:
      sum += links_weight[key]

    # print "sum of all links weight is: ", sum

    for key in links_weight:
      normailized_weight[key] = links_weight[key]/float(sum)
    if (DEBUG):
      print "final results are: ", normailized_weight
    return normailized_weight

# Given pages, for each page, convert all outlinks weight to inlinks weight
def create_in_links(pages):
  links_to_page = {}
  # initialize dict.
  for page in pages:
    arr = page._filename.split('/')
    name = arr[len(arr)-1]
    links_to_page[name] = []

  for page in pages:
    arr = page._filename.split('/')
    name = arr[len(arr)-1]
    for link in page._links_weight:
      links_to_page[link].append((name, page._links_weight[link]))

  return links_to_page


if __name__ == '__main__':
  parser = ArgumentParser(description="Please give input file directory and F value.")
  parser.add_argument('-docs', '-d',
                      type=str,
                      dest='dir',
                      required=True,
                      action='store',
                      help='please specify the directory for all input files.'
                      )
  parser.add_argument('-flip', '-f',
                      type=float,
                      dest='flip',
                      required=True,
                      action='store',
                      help='please provide the probability of flip a coin.'
                      )
  args = parser.parse_args()
  F = args.flip
  pages = []
  # /Users/BINLI/Documents/Course/Web-Search-Engine/PS/PS3/docs
  all_files = glob.glob(args.dir + "/*.html")

  N = len(all_files)
  epsilon = 0.01 / N
  # print "N is:", N

  sum = 0
  for file in all_files:
    page = Page(file)
    page._base = np.log2(page.wordcount())
    sum += page._base
    pages.append(page)

  # print "sum of page base is: ", sum, "\n"

  # initialize page score and calculate link weight.
  for page in pages:
    page._score = page._base/sum
    page._base = page._base/sum
    with open(page._filename) as f:
      contents = f.read()
      soup = BeautifulSoup(contents, "html.parser")
      links = soup.find_all('a')

      # if there is no outlinks, each link weight to other page is 1 / N
      if len(links) == 0:
        for file in all_files:
          arr = file.split('/')
          name = arr[len(arr)-1]
          page._links_weight[name] = 1 / N
      else:
        page._links_weight = page.calc_links_weight(links)

  # for page in pages:
  #   print page._filename
  #   print "page base is: ", page._base
  #   print "page score is: ", page._score
  #   print "all links weight is: ",page._links_weight, "\n"

  in_links_weight = create_in_links(pages)

  # print "in_links_weight is: ", in_links_weight

  CHANGED = True
  while(CHANGED):
    CHANGED = False
    count = 0
    for page in pages:
      count = count + 1
      # print count
      total_links_weight = 0
      # get the total weight of in links.
      arr = page._filename.split('/')
      name = arr[len(arr)-1]

      for tuple in in_links_weight[name]:
        for p in pages:
          arr = p._filename.split('/')
          pname = arr[len(arr)-1]
          # print "name is: ", pname, "tuple[0] is: ", tuple[0], "\n"
          if pname == tuple[0]:
            # print "The matched page's links weight and score are: "
            # print p._score
            total_links_weight += p._score * tuple[1]


      # print "Total links weight is: ", total_links_weight, "\n"
      # print "Page base is: ", page._base

      page._newscore = (1-F) * page._base + F * total_links_weight

      # print "epsilon is: ", epsilon
      # print "new score is: ", page._newscore
      # print "original score is: ", page._score

      if abs(page._newscore - page._score) > epsilon:
        CHANGED = True
    for page in pages:
      page._score = page._newscore

  # sort in place based on the specified attribute of an object
  pages.sort(key=lambda x : x._score, reverse=True)
  for page in pages:
    arr = page._filename.split('/')
    name = arr[len(arr)-1]
    print name, ": ", ("%.4f" % page._score)


