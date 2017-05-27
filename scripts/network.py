#!/usr/bin/env python

class hierarchical():

	def __init__(self):

		self.num_epochs = 1
		self.num_images = 200

		self.state = npy.zeros(5)
		self.parse_tree = []
		self.backward_indices = []
		self.rewards = []

	def initialize_tensorflow_model(self, sess):

		# Initializing the session.
		self.sess = sess

		# Image size and other architectural parameters. 
		self.image_size = 20
		self.conv1_size = 3	
		self.conv1_num_filters = 20

		self.conv2_size = 3	
		self.conv2_num_filters = 20

		# Placeholders
		self.input = tf.placeholder(tf.float32,shape=[None,self.image_size,self.image_size,1],name='input')

		# Convolutional layers: 
		# Layer 1
		self.W_conv1 = tf.Variable(tf.truncated_normal([self.conv1_size,self.conv1_size, 1, self.conv1_num_filters],stddev=0.1),name='W_conv1')
		self.b_conv1 = tf.Variable(tf.constant(0.1,shape=[self.conv1_num_filters]),name='b_conv1')
		self.conv1 = tf.add(tf.nn.conv2d(self.input,self.W_conv1,strides=[1,1,1,1],padding='VALID'),self.b_conv1,name='conv1')
		self.relu_conv1 = tf.nn.relu(self.conv1)

		# Layer 2 
		self.W_conv2 = tf.Variable(tf.truncated_normal([self.conv2_size,self.conv2_size,self.conv1_num_filters,self.conv2_num_filters],stddev=0.1),name='W_conv2')
		self.b_conv2 = tf.Variable(tf.constant(0.1,shape=[self.conv2_num_filters]),name='b_conv2')
		self.conv2 = tf.add(tf.nn.conv2d(self.relu_conv1,self.W_conv2,strides=[1,1,1,1],padding='VALID'),self.b_conv2,name='conv2')
		self.relu_conv2 = tf.nn.relu(self.conv2)

		# Layer 3
		self.W_conv3 = tf.Variable(tf.truncated_normal([self.conv3_size,self.conv3_size,self.conv2_num_filters,self.conv3_num_filters],stddev=0.1),name='W_conv3')
		self.b_conv3 = tf.Variable(tf.constant(0.1,shape=[self.conv3_num_filters]),name='b_conv3')
		self.conv3 = tf.add(tf.nn.conv2d(self.relu_conv2,self.W_conv3,strides=[1,1,1,1],padding='VALID'),self.b_conv3,name='conv3')
		self.relu_conv3 = tf.nn.relu(self.conv3)

		# Now going to flatten this and move to a fully connected layer.s
		self.fc_input_shape = 14*14
		self.relu_conv3_flat = tf.reshape(self.relu_conv3,[-1,self.fc_input_shape])

		# Going to split into 3 streams: RULE, SPLIT, and GOAL
		self.fcs1_l1_shape = 120
		self.W_fcs1_l1 = tf.Variable(tf.truncated_normal([self.fc_input_shape,self.fcs1_l1_shape],stddev=0.1),name='W_fcs1_l1')
		self.b_fcs1_l1 = tf.Variable(tf.constant(0.1,shape=[self.fcs1_l1_shape]),name='b_fcs1_l1')
		self.fcs1_l1 = tf.nn.relu(tf.add(tf.matmul(self.relu_conv3_flat,self.W_fsc1_l1),self.b_fcs1_l1),name='fcs1_l1')

		self.fcs2_l1_shape = 30
		self.W_fcs2_l1 = tf.Variable(tf.truncated_normal([self.fc_input_shape,self.fcs2_l1_shape],stddev=0.1),name='W_fcs2_l1')		
		self.b_fcs2_l1 = tf.Variable(tf.constant(0.1,shape=[self.fcs2_l1_shape]),name='b_fcs2_l1')
		self.fcs2_l1 = tf.nn.relu(tf.add(tf.matmul(self.relu_conv3_flat,self.W_fsc2_l1),self.b_fcs2_l1),name='fcs2_l1')		

		self.fcs3_l1_shape = 30
		self.W_fcs3_l1 = tf.Variable(tf.truncated_normal([self.fc_input_shape,self.fcs3_l1_shape],stddev=0.1),name='W_fcs3_l1')		
		self.b_fcs3_l1 = tf.Variable(tf.constant(0.1,shape=[self.fcs3_l1_shape]),name='b_fcs3_l1')
		self.fcs3_l1 = tf.nn.relu(tf.add(tf.matmul(self.relu_conv3_flat,self.W_fsc3_l1),self.b_fcs3_l1),name='fcs3_l1')		

		# 2nd FC layer: Output:
		self.number_primitives = 1
		self.fcs1_output_shape = 5*self.number_primitives+3
		self.W_fcs1_l2 = tf.Variable(tf.truncated_normal([self.fcs1_l1_shape,self.fcs1_output_shape],stddev=0.1),name='W_fcs1_l2')
		self.b_fcs1_l2 = tf.Variable(tf.truncated_normal(0.1,shape=[self.fcs1_output_shape]),name='b_fcs1_l2')
		self.fcs1_presoftmax = tf.add(tf.matmul(self.fcs1_l1,self.W_fcs1_l2),self.b_fcs1_l2,name='fcs1_presoftmax')
		self.rule_probabilities = tf.nn.softmax(self.fcs1_presoftmax,name='softmax')

		# Split output.
		self.W_split = tf.Variable(tf.truncated_normal([self.fcs2_l1_shape,2],stddev=0.1),name='W_split')
		self.b_split = tf.Variable(tf.constant(0.1,shape=[2]),name='b_split')
		
		self.fcs2_preslice = tf.matmul(self.fcs2_l1,self.W_split)+self.b_split
		self.split_mean = tf.nn.sigmoid(self.fcs2_preslice[0])
		self.split_cov = tf.nn.relu(self.fcs2_preslice[1])

		# Goal output.
		self.W_goal = tf.Variable(tf.truncated_normal([self.fcs3_l1_shape,4],stddev=0.1),name='W_goal')
		self.b_goal = tf.Variable(tf.constant(0.1,shape=[4]),name='b_goal')
		
		self.fcs3_preslice = tf.matmul(self.fcs3_l1,self.W_goal)+self.b_goal
		self.goal_mean = tf.nn.sigmoid(self.fcs3_preslice[:2])
		self.goal_cov = tf.nn.relu(self.fcs3_preslice[2:])		

		# CONSTRUCTING THE DISTRIBUTIONS FOR GOALS AND SPLITS
		self.goal_dist = tf.contrib.distributions.MultivariateNormalDiag(self.goal_mean,self.goal_cov)
		self.split_dist = tf.contrib.distributions.Normal(mu=self.split_mean,sigma=self.split_cov)

		# self.sample_goal = tf.placeholder(tf.float32,shape=(None,2),name='sample_goal')
		# self.sample_split = tf.placeholder(tf.float32,shape=(None,1),name='sample_split')

		# Sampling a goal and a split. Remember, this should still just be defining an operation, not actually sampling.
		self.sample_split = self.split_dist.sample()
		self.sample_goal = self.goal_dist.sample()

		# # # # # Defining training ops. 
		self.rule_return_weight = tf.placeholder(tf.float32,shape=(None,1),name='rule_return_weight')
		self.split_return_weight = tf.placeholder(tf.float32,shape=(None,1),name='split_return_weight')
		self.goal_return_weight = tf.placeholder(tf.float32,shape=(None,1),name='goal_return_weight')
		self.target_rule = tf.placeholder(tf.float32,shape=(None,self.fcs1_output_shape),name='target_rule')

		# Defining the loss for each of the 3 streams, rule, split and goal.
		# Rule loss is the negative cross entropy between the rule probabilities and the chosen rule as a one-hot encoded vector. 
		# Weighted by the return obtained. This is just the negative log probability of the selected action.
		self.rule_loss = -tf.multiply(tf.nn.softmax_cross_entropy_with_logits(labels=self.target_rule,logits=self.fcs1_presoftmax),self.rule_return_weight)

		# The split loss is the negative log probability of the chosen split, weighted by the return obtained.
		self.split_loss = -tf.multiply(self.split_dist.log_prob(self.sample_split),self.split_return_weight)

		# The goal loss is the negative log probability of the chosen goal, weighted by the return obtained.
		self.goal_loss = -tf.multiply(self.goal_dist.log_prob(self.sample_goal),self.goal_return_weight)

		# The total loss is the sum of individual losses.
		self.total_loss = self.rule_loss + self.split_loss + self.goal_loss

		# Creating a training operation to minimize the total loss.
		self.train = tf.train.AdamOptimizer(1e-4).minimize(self.total_loss,name='Adam_Optimizer')

		init = tf.global_variables_initializer()
		self.sess.run(init)

	# def calculate_returns(self):

	# def train_model(self):

	def reset_parse_tree(self):
		self.parse_tree = []
		self.rewards = []
		self.backward_indices = []

	def append_to_tree(self, state, reward, backward_index):
		self.parse_tree.append(state)
		self.rewards.append(reward)
		self.backward_indices.append(backward_index)

	def parse_nonterminal(self):
		# Pass a state nonterminal.
		self.image_input = self.images[i,self.state[1]:self.state[1]+self.state[3],self.state[2]:self.state[2]+self.state[4]]
		self.resized_image = cv2.resize(image_input,[self.image_size,self.image_size])

		rule_probabilities = self.sess.run([self.rule_probabilities], feed_dict={self.input: self.resized_image})
		
		# THIS IS THE RULE POLICY: This is a probabilistic selection of the rule., completely random.
		# Should it be an epsilon-greedy policy? 
		selected_rule = npy.random.choice(range(self.fcs1_output_shape),p=rule_probabilities)

		# If rules 0-5, need a split location.
		# If 6, need a goal location.

		# SAMPLING A SPLIT LOCATION
		if selected_rule<=5:
			split_location = self.sess.run([self.sample_split], feed_dict={self.input: self.resized_image})

			# Apply the rule.
			s1 = 

	def parse_primitive(self):
		# Pass a state primitive.

	def meta_training(self):

		# For all epochs
		for e in range(self.num_epochs):
			# For all images
			for i in range(self.num_images):

				# Intialize the parse tree for this image.
				image = self.images[i]

				# Remember the state is pixel label, then x origin, y origin, width, height.
				self.state = [0,0,0,self.image_size,self.image_size] 

				# Reset the parse tree, rewards, and backward indices. 
				self.reset_parse_tree()
				# Append the current state, 0 reward, and -1 to parse tree, rewards and backward indices respectively.
				self.append_to_tree(state,0,-1)

				# Forward pass of the rule policy- basically picking which rule.
				
				# If the current non-terminal is a shape.
				if (state==0):
					self.parse_nonterminal()

				# If the current non-terminal is a region assigned a particular primitive.
				if (state==1)or(state==2)or(state==3)or(state==4):
					self.parse_primitive()

	############################
	# Pixel labels: 
	# 0 for shape
	# 1 for shape with primitive 1
	# 2 for shape with primitive 2
	# 3 for shape with primitive 3
	# 4 for shape with primitive 4
	# 5 for region with no primitive (not to be painted)
	############################

	############################
	# Rule numbers:
	# 0 (Shape) -> (Shape) (Shape) 								(Vertical split)
	# 1 (Shape) -> (Shape (Shape) 								(Horizontal split)
	# 2 (Shape) -> (Region with primitive #) (Shape)			(Vertical split)
	# 3 (Shape) -> (Region with primitive #) (Shape)			(Horizontal split)
	# 4 (Shape) -> (Shape) (Region with primitive #) 			(Vertical split)
	# 5 (Shape) -> (Shape) (Region with primitive #) 			(Horizontal split)
	# 6 (Shape) -> (Region with primitive #) 
	# 7 (Shape) -> (Region not to be painted)
	############################

def main(args):

	# # Create a TensorFlow session with limits on GPU usage.
	# gpu_ops = tf.GPUOptions(allow_growth=True,visible_device_list="1,2")
	# config = tf.ConfigProto(gpu_options=gpu_ops)
	# sess = tf.Session(config=config)

	# If CPU:
	sess = tf.Session()

	hierarchical_model = hierarchical()
	hierarchical_model.initialize_tensorflow_model(sess)

if __name__ == '__main__':
	main(sys.argv)