#!/usr/bin/env python
from headers import *

class Model():

	def __init__(self, image_size=256):
		self.image_size = image_size

	def initialize_base_model(self, sess, model_file=None):

		# Initializing the session.
		self.sess = sess

		# Number of layers. 
		self.num_layers = 5
		self.num_fc_layers = 2
		self.conv_sizes = 3*npy.ones((self.num_layers),dtype=int)		
		self.conv_num_filters = npy.array([3,20,20,20,20,20],dtype=int)
		self.conv_strides = npy.array([1,2,2,2,2])

		# Placeholders
		self.input = tf.placeholder(tf.float32,shape=[1,self.image_size,self.image_size,3],name='input')

		# Defining conv layers.
		self.conv = [[] for i in range(self.num_layers)]

		# Initial layer.
		self.conv[0] = tf.layers.conv2d(self.input,filters=self.conv_num_filters[0],kernel_sizes=(self.conv_sizes[0]),activation=tf.nn.relu,name='conv0')

		# Defining subsequent conv layers.
		for i in range(1,self.num_layers):
			self.conv[i] = tf.layers.conv2d(self.conv[i-1],filters=self.conv_num_filters[i],kernel_sizes=(self.conv_sizes[i]),activation=tf.nn.relu,name='conv{0}'.format(i))

		# Now going to flatten this and move to a fully connected layer. 		
		self.flat_conv = tf.layers.flatten(self.conv[-1])

	def define_split_stream(self):

		self.fc6_shape = 200
		self.fc6 = tf.layers.dense(self.flat_conv,self.fc6_shape,activation=tf.nn.relu)

		# Split output.
		self.split_mean = tf.layers.dense(self.fc6,1,activation=tf.nn.sigmoid)
		if self.to_train:
			self.split_cov = 0.1
		else:
			self.split_cov = 0.001

		self.split_dist = tf.contrib.distributions.Normal(loc=self.split_mean,scale=self.split_cov)
		# Also maintaining placeholders for scaling, converting to integer, and back to float.
		self.sampled_split = tf.placeholder(tf.float32,shape=(None),name='sampled_split')

	def training_ops(self):
		self.split_return_weight = tf.placeholder(tf.float32,shape=(None),name='split_return_weight')
		self.split_loss = -tf.multiply(self.split_dist.log_prob(self.sampled_split),self.split_return_weight)

		# Creating a training operation to minimize the total loss.
		self.optimizer = tf.train.AdamOptimizer(1e-4)
		self.train = self.optimizer.minimize(self.split_loss,name='Adam_Optimizer')

		# Writing graph and other summaries in tensorflow.
		self.writer = tf.summary.FileWriter('training',self.sess.graph)
		init = tf.global_variables_initializer()
		self.sess.run(init)
	
	def model_load(self, model_file)
		#################################
		if model_file:
			# DEFINING CUSTOM LOADER:
			print("RESTORING MODEL FROM:", model_file)
			reader = tf.train.NewCheckpointReader(model_file)
			saved_shapes = reader.get_variable_to_shape_map()
			var_names = sorted([(var.name, var.name.split(':')[0]) for var in tf.global_variables()
				if var.name.split(':')[0] in saved_shapes])
			restore_vars = []
			name2var = dict(zip(map(lambda x:x.name.split(':')[0], tf.global_variables()), tf.global_variables()))
			with tf.variable_scope('', reuse=True):
				for var_name, saved_var_name in var_names:
					curr_var = name2var[saved_var_name]
					var_shape = curr_var.get_shape().as_list()
					if var_shape == saved_shapes[saved_var_name]:
						restore_vars.append(curr_var)
			saver = tf.train.Saver(max_to_keep=None,var_list=restore_vars)
			saver.restore(self.sess, model_file)
		#################################

	def create_network(self, sess, load_pretrained_mod=False, pretrained_weight_file=None):

		print("Training Policy from base model.")
		self.initialize_base_model(sess)
		self.define_split_stream()
		self.training_ops()

		if load_pretrained_mod:
			self.model_load(pretrained_weight_file)