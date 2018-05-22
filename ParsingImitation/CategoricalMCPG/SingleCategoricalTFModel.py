#!/usr/bin/env python
from headers import *

class Model():

	def __init__(self, image_size=256, num_channels=1):
		self.image_size = image_size
		self.num_channels = num_channels
		self.num_layers = 7

	def initialize_base_model(self, sess, model_file=None, to_train=None):

		# Initializing the session.
		self.sess = sess
		self.to_train = to_train

		# Number of layers. 
		self.num_fc_layers = 2
		self.conv_sizes = 3*npy.ones((self.num_layers),dtype=int)		
		self.conv_num_filters = 20*npy.ones((self.num_layers),dtype=int)
		self.conv_strides = 2*npy.ones((self.num_layers),dtype=int)

		self.conv_strides[0:3] = 1
		# # Strides are now: 1,1,1,2,2,2,2

		# Placeholders
		# Now doing this for single channel images.
		self.input = tf.placeholder(tf.float32,shape=[None,self.image_size,self.image_size,self.num_channels],name='input')

		# Defining conv layers.
		self.conv = [[] for i in range(self.num_layers)]

		# Initial layer.
		self.conv[0] = tf.layers.conv2d(self.input,filters=self.conv_num_filters[0],kernel_size=(self.conv_sizes[0]),strides=(self.conv_strides[0]),activation=tf.nn.relu,name='conv0')

		# Defining subsequent conv layers.
		for i in range(1,self.num_layers):
			self.conv[i] = tf.layers.conv2d(self.conv[i-1],filters=self.conv_num_filters[i],kernel_size=(self.conv_sizes[i]),strides=(self.conv_strides[i]),activation=tf.nn.relu,name='conv{0}'.format(i))

		# Now going to flatten this and move to a fully connected layer. 		
		self.flat_conv = tf.layers.flatten(self.conv[-1])

	def define_rule_stream(self):
		self.rule_fc5_shape = 1000
		self.rule_fc6_shape = 200
		self.rule_fc5 = tf.layers.dense(self.flat_conv,self.rule_fc5_shape,activation=tf.nn.relu)
		self.rule_fc6 = tf.layers.dense(self.rule_fc5,self.rule_fc6_shape,activation=tf.nn.relu)

		self.num_rules = 4
		self.rule_presoftmax = tf.layers.dense(self.rule_fc6,self.num_rules)
		self.premask_probabilities = tf.nn.softmax(self.rule_presoftmax,name='premask_probabilities')

		self.rule_mask = tf.placeholder(tf.float32,shape=(None,self.num_rules))
		self.prenorm_masked_probabilities = tf.multiply(self.premask_probabilities,self.rule_mask)
		self.prenorm_mask_sum = tf.reduce_sum(self.prenorm_masked_probabilities,axis=-1,keep_dims=True)
		self.rule_probabilities = tf.divide(self.prenorm_masked_probabilities,self.prenorm_mask_sum)

		self.rule_dist = tf.contrib.distributions.Categorical(probs=self.rule_probabilities,allow_nan_stats=False)
		self.sampled_rule = self.rule_dist.sample()
		self.rule_return_weight = tf.placeholder(tf.float32,shape=(None,1),name='rule_return_weight')

		self.target_rule = tf.placeholder(tf.float32,shape=(None,self.num_rules),name='target_rule')
		self.rule_cross_entropy = tf.keras.backend.categorical_crossentropy(self.target_rule,self.rule_probabilities)
		# self.rule_loss = tf.keras.backend.categorical_crossentropy(self.target_rule,self.rule_probabilities)
		# self.rule_loss = tf.multiply(self.rule_return_weight,self.rule_cross_entropy)
		self.rule_loss =  tf.multiply(self.rule_return_weight,tf.expand_dims(self.rule_cross_entropy,axis=-1))

	def define_split_stream(self):
		self.fc5_shape = 1000
		self.fc6_shape = 400
		self.fc5 = tf.layers.dense(self.flat_conv,self.fc5_shape,activation=tf.nn.relu)
		self.fc6 = tf.layers.dense(self.fc5,self.fc6_shape,activation=tf.nn.relu)
	
		self.split_mask = tf.placeholder(tf.float32,shape=(None,self.image_size-1),name='split_mask')

		self.preprobs = tf.layers.dense(self.fc6,self.image_size-1,activation=tf.nn.softmax)
		# self.preprobs = tf.layers.dense(self.fc6,self.image_size-1,activation=tf.nn.sigmoid)
		self.masked_probs = tf.multiply(self.split_mask,self.preprobs,name='masked_probs')

		self.masked_sum = tf.reduce_sum(self.masked_probs,axis=-1,name='masked_sum',keep_dims=True)
		self.masked_norm_probs = tf.divide(self.masked_probs,self.masked_sum,name='masked_norm_probs')

		self.split_dist = tf.contrib.distributions.Categorical(probs=self.masked_norm_probs,name='split_dist',allow_nan_stats=False)
		self.sample_dist = self.split_dist.sample()

		# # # Also maintaining placeholders for scaling, converting to integer, and back to float.
		# self.sampled_split = tf.placeholder(tf.int32,shape=(None,),name='sampled_split')

		# Defining return weight and loss. Evaluate the likelihood of a particular sample.
		self.split_return_weight = tf.placeholder(tf.float32,shape=(None,1),name='split_return_weight')
		# self.split_loglikelihood = self.split_dist.log_prob(self.sampled_split)
		# self.split_loss = -tf.multiply(self.split_loglikelihood,self.split_return_weight,name='split_loss')
	
		self.target_splits = tf.placeholder(tf.float32,shape=(None,self.image_size-1),name='target_splits')
		self.split_cross_entropy = tf.keras.backend.categorical_crossentropy(self.target_splits,self.masked_norm_probs)

		self.split_loss = -tf.multiply(self.split_return_weight,tf.expand_dims(self.split_cross_entropy,axis=-1),name='split_loss')

	def logging_ops(self):
		if self.to_train:
			# Create file writer to write summaries. 		
			self.tf_writer = tf.summary.FileWriter('train_logging'+'/',self.sess.graph)

			# Create summaries for: Log likelihood, reward weight, and total reward on the full image. 
			# self.split_loglikelihood_summary = tf.summary.scalar('Split_LogLikelihood',tf.reduce_mean(self.split_loglikelihood))
			self.rule_loglikelihood_summary = tf.summary.scalar('Rule_LogLikelihood',tf.reduce_mean(self.rule_cross_entropy))
			self.reward_weight_summary = tf.summary.scalar('Reward_Weight',tf.reduce_mean(self.rule_return_weight))

			# Merge summaries. 
			self.merged_summaries = tf.summary.merge_all()		

	def training_ops(self):

		self.total_loss = self.rule_loss+self.split_loss
		# self.total_loss = self.split_loss

		# Creating a training operation to minimize the total loss.
		self.optimizer = tf.train.AdamOptimizer(1e-4)

		# Clipping gradients because of NaN values. 
		self.gradients_vars = self.optimizer.compute_gradients(self.total_loss)
		self.clipped_gradients = [(tf.clip_by_norm(grad,10),var) for grad, var in self.gradients_vars]
		self.train = self.optimizer.apply_gradients(self.clipped_gradients)

		# Writing graph and other summaries in tensorflow.
		self.writer = tf.summary.FileWriter('training',self.sess.graph)
		init = tf.global_variables_initializer()
		self.sess.run(init)
	
	def model_load(self, model_file):
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

	def save_model(self, model_index, iteration_number=-1):
		if not(os.path.isdir("saved_models")):
			os.mkdir("saved_models")

		self.saver = tf.train.Saver(max_to_keep=None)           

		if not(iteration_number==-1):
			save_path = self.saver.save(self.sess,'saved_models/model_epoch{0}_iter{1}.ckpt'.format(model_index,iteration_number))
		else:
			save_path = self.saver.save(self.sess,'saved_models/model_epoch{0}.ckpt'.format(model_index))

	def create_network(self, sess, pretrained_weight_file=None, to_train=False):

		self.initialize_base_model(sess,to_train=to_train)
		self.define_rule_stream()
		self.define_split_stream()
		self.logging_ops()
		self.training_ops()

		if pretrained_weight_file:
			self.model_load(pretrained_weight_file)