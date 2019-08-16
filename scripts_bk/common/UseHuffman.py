from HuffmanCoding import HuffmanCoding

#input file path
path = "./sample.txt"

h = HuffmanCoding(path)

output_path = h.compress()
h.decompress(output_path)

