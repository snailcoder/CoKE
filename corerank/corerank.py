#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import math
import copy
import argparse

import igraph

# Reimplement min heap according to Introduction to Algorithms (3rd Edition).
# Python heapq is great, however, it's necessary to track
def parent(i):
  return (i - 1) // 2

def left(i):
  return 2 * i + 1

def right(i):
  return 2 * (i + 1)

def min_heapify(h, i, vindex):
  l = left(i)
  r = right(i)
  smallest = i
  if l < len(h) and h[l] < h[i]:
    smallest = l
  if r < len(h) and h[r] < h[smallest]:
    smallest = r
  if smallest != i:
    # h: [['a', 5], ['b', 2]] => [['b', 2], ['a', 5]]
    h[i], h[smallest] = h[smallest], h[i]
    # vindex: {['a', 5]: 1, ['b', 2]: 0} => {['a', 5]: 0, ['b', 2]: 1}
    vindex[h[i][1]], vindex[h[smallest][1]] = vindex[h[smallest][1]], vindex[h[i][1]]
    min_heapify(h, smallest, vindex)

def build_min_heap(h, vindex):
  for i in range(len(h) // 2 - 1, -1, -1):
    min_heapify(h, i, vindex)

def heap_extract_min(h, vindex):
  if len(h) == 0:
    raise IndexError('heap is empty')
  top = h[0]
  h[0] = h[-1]
  vindex[h[0][1]] = 0
  h.pop()
  vindex.pop(top[1])
  min_heapify(h, 0, vindex)
  return top

def heap_decrease_key(h, i, key, vindex):
  if key > h[i][0]:
    raise ValueError('new key is greater than current key')

  h[i][0] = key
  while i > 0 and h[i][0] < h[parent(i)][0]:
    p = parent(i)
    h[i], h[p] = h[p], h[i]
    vindex[h[i][1]], vindex[h[p][1]] = vindex[h[p][1]], vindex[h[i][1]]
    i = p

def build_graph_of_words(words, win_size):
  win = words[:win_size]
  edges = {}

  for i in range(win_size):
    for j in range(i + 1, win_size):
      v1, v2 = win[i], win[j]
      # We need simple graph: no loop or multiple edges are permitted
      if v1 == v2:
        continue
      if (v1, v2) in edges:
        edges[(v1, v2)] += 1
      elif (v2, v1) in edges:
        edges[(v2, v1)] += 1
      else:
        edges[(v1, v2)] = 1

  for i in range(win_size, len(words)):
    win = words[i - win_size + 1:i + 1]
    v2 = win[-1]
    for j in range(win_size - 1):
      v1 = win[j]
      if v1 == v2:
        continue
      if (v1, v2) in edges:
        edges[(v1, v2)] += 1
      elif (v2, v1) in edges:
        edges[(v2, v1)] += 1
      else:
        edges[(v1, v2)] = 1

  g = igraph.Graph()  # Undirected word co-occurrence network

  g.add_vertices(sorted(set(words)))  # Unique words
  g.add_edges(edges.keys())

  g.es['weight'] = list(edges.values())
  g.vs['weight'] = g.strength(weights=list(edges.values()))

  return g

def k_core_decomposition(g):
  gc = copy.deepcopy(g)
  core = {v: 0 for v in gc.vs['name']}
  p = [list(a) for a in zip(gc.strength(gc.vs['name'], weights=gc.es['weight']), gc.vs['name'])]
  vindex = {v: i for i, v in enumerate(gc.vs['name'])}  # initial indeices
  build_min_heap(p, vindex)
  while len(p) > 0:
    top = heap_extract_min(p, vindex)
    core[top[1]] = top[0]
    neighbors = gc.vs[gc.neighbors(top[1])]['name']
    gc.delete_vertices(top[1])
    for v in neighbors:
      key = max(top[0], gc.strength(v, weights=gc.es['weight']))
      heap_decrease_key(p, vindex[v], key, vindex)

  return core

def core_rank(v, g, core):
  neighbors = g.vs[g.neighbors(v)]['name']
  return sum([core[neigh] for neigh in neighbors])

def comb(n, k):
  return math.factorial(n) // math.factorial(k) // math.factorial(n - k)

def keyword_quality(keywords, g, core, l):
  score = sum([core_rank(kw, g, core) for kw in keywords])
  sg = g.induced_subgraph(keywords)
  h = 0
  if sg.vcount() >= 2:
    h = comb(sg.vcount(), 2) - sg.ecount()
  return score - l * h

def optimize(words, g, core, l, k):
  words = set(words)
  best_keywords = set()
  best_quality = 0
  for i in range(k):
    max_gain = 0
    best_word = None
    for w in sorted(words):
      quality = keyword_quality(best_keywords | set([w]), g, core, l)
      gain = quality - best_quality
      if gain > max_gain:
        max_gain = gain
        best_word = w
    if best_word is None:
      raise ValueError('no word selected')
    best_quality += max_gain
    best_keywords.add(best_word)
    words.remove(best_word)

  return best_keywords

# words = ['mathematical', 'aspects', 'computer-aided', 'share', 'trading', 'problems', 'statistical', 'analysis', 'share', 'price', 'probabilistic', 'characteristics', 'price', 'series', 'methods', 'mathematical', 'modelling', 'price', 'series', 'probabilistic', 'characteristics']
# win_size = 3
# 
# g = build_graph_of_words(words, win_size)
# core = k_core_decomposition(g)
# # print(core)
# # assert(g['price', 'probabilistic'] == 5)
# # assert(g['price', 'series'] == 5)
# 
# keywords = optimize(words, g, core, 0.1, 3)
# print(keywords)

parser = argparse.ArgumentParser(
    description='Extract keywords with k-core decomposition.')
parser.add_argument('document',
                    help='a processed text file, one document per line,'
                         ' words are separated by space')
parser.add_argument('output',
                    help='the keywords file, one keyword set per line')
parser.add_argument('-w', type=int, default=3,
                    help='sliding window of graph of words')
parser.add_argument('-l', type=float, default=0.1,
                    help='a trade-off parameter of keywords quality function')
parser.add_argument('-k', type=int, default=3,
                    help='the number of keywords you want')

args = parser.parse_args()

with open(args.document, 'r') as fi, open(args.output, 'w') as fo:
  for line in fi:
    line = line.strip()
    if not line:
      continue
    words = line.split()
    g = build_graph_of_words(words, args.w)
    core = k_core_decomposition(g)
    keywords = optimize(words, g, core, args.l, args.k)
    fo.write('%s\n' % ' '.join(sorted(keywords)))

