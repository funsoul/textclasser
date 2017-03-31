#!/usr/bin/python
#-*-coding:utf-8-*-

import jieba
import os
import shutil 
import math
from contextlib import nested

import sys
reload(sys)
sys.setdefaultencoding('utf-8')

class textinfo():
	"""
		file info of certain class, created for tf-idf.
		max_word_num: max number of words in the class file
		file_num: the number of files in the class
		wordmap: key is word, and value is list which size is 2
		        list[0] save wordcount, and list[1] saves tf-idf
	"""

	def __init__(self):
		# save file num of the class
		self.file_num = 0
		#word map key is word, and value is list which size is 2
		#list[0] save wordcount in this class texts, list[1] is tf-idf
		self.wordmap = {}
		self.max_word_num = 0

	def update(self, words):
		"""
			update class info in this function
			words: the new word list added
		"""
		
		self.file_num += 1

		flags = {}
		for w in words:
			if w not in self.wordmap:
				self.wordmap[w] = [0, 0]
			self.wordmap[w][0] += 1
			if self.wordmap[w][0] > self.max_word_num:
				self.max_word_num = self.wordmap[w][0]
		return

	def tf_idf(self,w, number_in_set, text_num):
		"""
			compute word`s tf_idf
		"""
		
		tf = 1.0 * self.wordmap[w][0] / self.max_word_num
		idf = math.log(1.0*text_num/(number_in_set+1)) 
		#print "tf is %f , idf is %f " %  (tf, idf)
		self.wordmap[w][1] = tf * idf
		return

	def get_mainwords(self, n=500):
		"""
			get n words from wordmap, which sorted by tf-idf
			sort wordmap first, return n words list,
			should called after tf_idf function
		"""
		
		#sort wordmap by tf-idf, sorted list is list of tuple ("key", list)
		sorted_list = sorted(self.wordmap.items(), key=lambda d:d[1][1], reverse=True)

		words_list = []
		assert len(sorted_list) >= n, "main words num n must > all words num in text."
		for i in range(0, n):
			words_list.append(sorted_list[i][0])
			
		return words_list


class dataset():
	"""
		data preparation class,
		1. text split using jieba
		2. delete same and stop words.
		2. generate dict.
		3. generate data(test and train) vector.
	"""
	def __init__(self):
		pass

	def get_unique_id(self, data_dir):
		"""
			get flie unique id famate as {class_id}_type_{text_id}.txt.
			data_dir is the full path of file
		  	e.g ./training_set/4_tec/4_tec_text/text_2001.txt
			where "training" is type, "4" is file class, and "2001" is text id.
			modify this function to adapt your data dir fomate
		"""
		
		dir_list = data_dir.split("/")
		class_id = dir_list[2].split("_")[0]
		text_id = dir_list[4].split(".")[0]
		type_id = dir_list[1].split("_")[0]
		return class_id + "_" + type_id + "_" + text_id

	def splitwords(self, data_dir, data_type):
		""" 
			split word for all files under data_dir 
			save data as <class_{data_type}_id> <words> in ./{data_type}_file2words.txt,
			where data_type is train, test or cv.
			output: {data_type}.txt includes all map of  file unique id and file words.
		"""
		
		if os.path.exists(data_type+".txt"):
			os.remove(data_type+".txt")
		
		list_dirs = os.walk(data_dir)
		for root, _, files in list_dirs:
			# get all files under data_dir
			for fp in files:
				file_path = os.path.join(root, fp)
				file_id = self.get_unique_id(file_path)
				#split words for f, save in file ./data_type.txt
				with nested(open(file_path), open(data_type+".txt", "a+")) as (f1, f):
					data = f1.read()
					#print data
					seg_list = jieba.cut(data, cut_all=False)
					f2.write(file_id + " " + " ".join(seg_list).replace("\n", " ")+"\n")
		
		print "split word for %s file end." % data_type
		return

	def rm_stopwords(self, file_path, word_dict):
		"""
			rm stop word for {file_path}, stop words save in {word_dict} file.
			file_path: file path of file generated by function splitwords.
						each lines of file is format as <file_unique_id> <file_words>. 
			word_dict: file containing stop words, and every stop words in one line.
			output: file_path which have been removed stop words and overwrite original file.
		"""
		
		#read stop word dict and save in stop_dict
		stop_dict = {}
		with open(word_dict) as d:
			for word in d:
				stop_dict[word.strip("\n")] = 1
		
		# remove tmp file if exists
		if os.path.exists(file_path+".tmp"):
			os.remove(file_path+".tmp")
	
		print "now remove stop words in %s." % file_path
		# read source file and rm stop word for each line.
		with nested(open(file_path), open(file_path+".tmp", "a+"))  as (f1, f2):
			for line in f1:
				tmp_list = [] # save words not in stop dict
				words = line.split()[1:]
				for word in words:
					if word not in stop_dict:
						tmp_list.append(word)
				words_without_stop =  " ".join(tmp_list)
				f2.write(words_without_stop + "\n")
		
		# overwrite origin file with file been removed stop words
		shutil.move(file_path+".tmp", file_path)
		print "stop words in %s has been removed." % file_path
		return

	def gen_dict(self, file_path, save_path="../dict/word_dict.txt"):
		"""
			generate key words dict for text using tf_idf algrithm.
			file_path: file have been removed stop words, each lines 
					   of file is format as <file_unique_id> <file_words>.
			output: word_dict.txt, each line in this file is a word
		"""

		#save textinfo by class id 
		class_dict = {}
		# all train text num
		text_num = 0
		# save map of word and number of files includes the word
		word_in_files = {}
		with open(file_path) as f:
			for line in f:
				text_num += 1
				words = line.split()
				#words[0] is {class_id}_type_id
				class_id = words[0].split("_")[0]
				if class_id not in class_dict:
					class_dict[class_id] = textinfo()
					
				class_dict[class_id].update(words[1:])
				
				# update word_in_files
				flags = {}
				for w in words[1:]:
					if w not in word_in_files:
						word_in_files[w] = 0
					if w not in flags:
						flags[w] = False
				
					if flags[w] is False:
						word_in_files[w] += 1
						flags[w] = True
			print "save textinfo according to class id over"
	
		if os.path.exists(save_path):
			os.remove(save_path)
			
		for k, text_info in class_dict.items():
			#print "class %s has %d words" % (k, text_info.file_num)
			# get tf in words of class k
			for w in text_info.wordmap:
				text_info.tf_idf(w, word_in_files[w], text_num)

			main_words = []
			with open(save_path, "a+") as f:
				main_words = text_info.get_mainwords()
				print "class %s : main words num: %d" % (k, len(main_words))
				f.write("\n".join(main_words) + "\n")
		
		print "gen word dict in %s." % save_path
		return

	def gen_wordbag(self, file_path, word_dict="../dict/word_dict.txt"):
		"""
			generate wordbag using word_dict.txt.
			output: {data_type_bag.txt}, lines in the file is
				<file_unique_id> <words_vector>. each position of
				words_vector is match the word_dict.txt. the vaklue 
				of words_vector is number of words appearing in file.
				
		"""

		#read word_dict.txt
		dict_list = []
		with open(word_dict) as d:
			for line in d:
				dict_list.append(line.strip("\n"))
		
		# remove tmp file if exists
		if os.path.exists(file_path+".tmp"):
			os.remove(file_path+".tmp")
	
		#gen vector fomate of data_set, overwrite origin {file_path}
		with nested(open(file_path), open(file_path+".tmp", "a+")) as (f1, f2):
			for line in f1:
				# tmp vector of one text
				word_vector = []
				for i in range(0, len(dict_list)):
					word_vector.append(0)
				words = line.split()
				#words[0] is {class_id}_type_id
				class_id = words[0].split("_")[0]
				for w in words[1:]:
					if w in dict_list:
						word_vector[dict_list.index(w)] += 1
				
				f2.write(class_id + " " + " ".join(map(str, word_vector)) + "\n")

		shutil.move(file_path+".tmp", file_path)
		print "gen word bag over of %s." % file_path
		return 
				

if __name__ == '__main__':
	data_pre = dataset()
	#data_pre.splitwords("../training_set", "train")
	#data_pre.rm_stopwords("train.txt", "../dict/stop_words_ch.txt")
	#data_pre.gen_dict("train.txt")
	data_pre.gen_wordbag("train.txt")
