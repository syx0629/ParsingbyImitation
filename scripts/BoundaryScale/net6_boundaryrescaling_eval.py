#!/usr/bin/env python
from headers import *
from state_class import *

class hierarchical():

	def __init__(self):

		self.num_epochs = 1
		self.num_images = 20000
		self.current_parsing_index = 0
		self.parse_tree = [parse_tree_node()]
		self.paintwidth = int(sys.argv[3])
		self.minimum_width = int(sys.argv[4])
		self.images = []
		self.true_labels = []
		self.image_size = 20
		self.predicted_labels = npy.zeros((self.num_images,self.image_size, self.image_size))
		self.painted_images = -npy.ones((self.num_images, self.image_size,self.image_size))

	def initialize_tensorflow_model(self, sess, model_file=None):

		# Initializing the session.
		self.sess = sess

		# Image size and other architectural parameters. 
		self.conv1_size = 3	
		self.conv1_num_filters = 20
		self.conv2_size = 3	
		self.conv2_num_filters = 20
		self.conv3_size = 3	
		self.conv3_num_filters = 20
		self.conv4_size = 3	
		self.conv4_num_filters = 20
		self.conv5_size = 3	
		self.conv5_num_filters = 20

		# Placeholders
		self.input = tf.placeholder(tf.float32,shape=[1,self.image_size,self.image_size,1],name='input')

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

		# Layer 4
		self.W_conv4 = tf.Variable(tf.truncated_normal([self.conv4_size,self.conv4_size,self.conv3_num_filters,self.conv4_num_filters],stddev=0.1),name='W_conv4')
		self.b_conv4 = tf.Variable(tf.constant(0.1,shape=[self.conv4_num_filters]),name='b_conv4')
		if self.image_size == 20:
			self.conv4 = tf.add(tf.nn.conv2d(self.relu_conv3,self.W_conv4,strides=[1,1,1,1],padding='VALID'),self.b_conv4,name='conv4')
		else:
			self.conv4 = tf.add(tf.nn.conv2d(self.relu_conv3,self.W_conv4,strides=[1,2,2,1],padding='VALID'),self.b_conv4,name='conv4')
		self.relu_conv4 = tf.nn.relu(self.conv4)

		# Layer 5
		self.W_conv5 = tf.Variable(tf.truncated_normal([self.conv5_size,self.conv5_size,self.conv4_num_filters,self.conv5_num_filters],stddev=0.1),name='W_conv5')
		self.b_conv5 = tf.Variable(tf.constant(0.1,shape=[self.conv5_num_filters]),name='b_conv5')
		# if self.image_size == 20:
			# self.conv5 = tf.add(tf.nn.conv2d(self.relu_conv4,self.W_conv5,strides=[1,1,1,1],padding='VALID'),self.b_conv5,name='conv5')
			# self.conv5 = tf.add(tf.nn.conv2d(self.relu_conv4,self.W_conv5,strides=[1,2,2,1],padding='VALID'),self.b_conv5,name='conv5')	
		# else:
		self.conv5 = tf.add(tf.nn.conv2d(self.relu_conv4,self.W_conv5,strides=[1,2,2,1],padding='VALID'),self.b_conv5,name='conv5')	
		self.relu_conv5 = tf.nn.relu(self.conv5)

		# Now going to flatten this and move to a fully connected layer.s
		if self.image_size==20:
			self.fc_input_shape = 5*5*self.conv5_num_filters
		else:
			self.fc_input_shape = 10*10*self.conv5_num_filters
		self.relu_conv5_flat = tf.reshape(self.relu_conv5,[-1,self.fc_input_shape])
		
		#Splitting into 3 streams: Choosing Rules, Splits, and Primitives		
		
		# STARTING RULE STREAM:
		# Now not using the start and goal
		self.fcs1_l1_shape = 120
		self.W_fcs1_l1 = tf.Variable(tf.truncated_normal([self.fc_input_shape,self.fcs1_l1_shape],stddev=0.1),name='W_fcs1_l1')
		self.b_fcs1_l1 = tf.Variable(tf.constant(0.1,shape=[self.fcs1_l1_shape]),name='b_fcs1_l1')
		self.fcs1_l1 = tf.nn.relu(tf.add(tf.matmul(self.relu_conv5_flat,self.W_fcs1_l1),self.b_fcs1_l1),name='fcs1_l1')

		# self.fcs1_output_shape = 1*self.number_primitives+5
		self.fcs1_output_shape = 6
		self.W_fcs1_l2 = tf.Variable(tf.truncated_normal([self.fcs1_l1_shape,self.fcs1_output_shape],stddev=0.1),name='W_fcs1_l2')
		self.b_fcs1_l2 = tf.Variable(tf.constant(0.1,shape=[self.fcs1_output_shape]),name='b_fcs1_l2')
		self.fcs1_presoftmax = tf.add(tf.matmul(self.fcs1_l1,self.W_fcs1_l2),self.b_fcs1_l2,name='fcs1_presoftmax')
		self.rule_probabilities = tf.nn.softmax(self.fcs1_presoftmax,name='softmax')

		# STARTING SPLIT STREAM:
		self.fcs2_l1_shape = 50
		self.W_fcs2_l1 = tf.Variable(tf.truncated_normal([self.fc_input_shape,self.fcs2_l1_shape],stddev=0.1),name='W_fcs2_l1')		
		self.b_fcs2_l1 = tf.Variable(tf.constant(0.1,shape=[self.fcs2_l1_shape]),name='b_fcs2_l1')
		self.fcs2_l1 = tf.nn.relu(tf.add(tf.matmul(self.relu_conv5_flat,self.W_fcs2_l1),self.b_fcs2_l1),name='fcs2_l1')		

		# Split output.
		self.W_split = tf.Variable(tf.truncated_normal([self.fcs2_l1_shape,2],stddev=0.1),name='W_split')
		self.b_split = tf.Variable(tf.constant(0.1,shape=[2]),name='b_split')
		self.fcs2_preslice = tf.matmul(self.fcs2_l1,self.W_split)+self.b_split
		self.split_mean = tf.nn.sigmoid(self.fcs2_preslice[0,0])
		# self.split_cov = tf.nn.softplus(self.fcs2_preslice[0,1])+0.05
		self.split_cov = 0.1
		# self.split_cov = 0.01
		self.split_dist = tf.contrib.distributions.Normal(loc=self.split_mean,scale=self.split_cov)

		# STARTING PRIMITIVE STREAM:		
		self.number_primitives = 4
		self.primitivefc_l1_shape = 50
		self.W_primitivefc_l1 = tf.Variable(tf.truncated_normal([self.fc_input_shape,self.primitivefc_l1_shape],stddev=0.1),name='W_primitivefc_l1')
		self.b_primitivefc_l1 = tf.Variable(tf.constant(0.1,shape=[self.primitivefc_l1_shape]),name='b_primitivefc_l1')
		self.primitivefc_l1 = tf.nn.relu(tf.add(tf.matmul(self.relu_conv5_flat,self.W_primitivefc_l1),self.b_primitivefc_l1),name='primitivefc_l1')

		self.W_primitivefc_l2 = tf.Variable(tf.truncated_normal([self.primitivefc_l1_shape, self.number_primitives],stddev=0.1),name='W_primitivefc_l2')
		self.b_primitivefc_l2 = tf.Variable(tf.constant(0.1,shape=[self.number_primitives]),name='b_primitivefc_l2')
		self.primitivefc_presoftmax = tf.add(tf.matmul(self.primitivefc_l1,self.W_primitivefc_l2),self.b_primitivefc_l2,name='primitivefc_presoftmax')
		self.primitive_probabilities = tf.nn.softmax(self.primitivefc_presoftmax,name='primitive_softmax')

		# Sampling a goal and a split. Remember, this should still just be defining an operation, not actually sampling.
		# We evaluate this to retrieve a sample goal / split location. 
		self.sample_split = self.split_dist.sample()

		# Also maintaining placeholders for scaling, converting to integer, and back to float.
		self.sampled_split = tf.placeholder(tf.float32,shape=(None),name='sampled_split')

		# Defining training ops. 
		self.rule_return_weight = tf.placeholder(tf.float32,shape=(None),name='rule_return_weight')
		self.split_return_weight = tf.placeholder(tf.float32,shape=(None),name='split_return_weight')
		self.primitive_return_weight = tf.placeholder(tf.float32,shape=(None),name='primitive_return_weight')
		self.target_rule = tf.placeholder(tf.float32,shape=(self.fcs1_output_shape),name='target_rule')
		self.target_primitive = tf.placeholder(tf.float32,shape=(self.number_primitives),name='target_primitive')

		self.previous_goal = npy.zeros(2)
		self.current_start = npy.zeros(2)

		# Rule loss is the negative cross entropy between the rule probabilities and the chosen rule as a one-hot encoded vector. 
		# Weighted by the return obtained. This is just the negative log probability of the selected action.
		self.rule_loss = tf.multiply(tf.nn.softmax_cross_entropy_with_logits(labels=self.target_rule,logits=self.fcs1_presoftmax),self.rule_return_weight)
 
		# The split loss is the negative log probability of the chosen split, weighted by the return obtained.
		self.split_loss = -tf.multiply(self.split_dist.log_prob(self.sampled_split),self.split_return_weight)

		# Primitive loss
		# self.primitive_loss = tf.multiply(tf.nn.softmax_cross_entropy_with_logits(labels=self.target_primitive,logits=self.primitive_probabilities),self.primitive_return_weight)
		self.primitive_loss = tf.multiply(tf.nn.softmax_cross_entropy_with_logits(labels=self.target_primitive,logits=self.primitivefc_presoftmax),self.primitive_return_weight)

		# The total loss is the sum of individual losses.
		self.total_loss = self.rule_loss + self.split_loss + self.primitive_loss

		# Creating a training operation to minimize the total loss.
		self.optimizer = tf.train.AdamOptimizer(1e-4)
		self.train = self.optimizer.minimize(self.total_loss,name='Adam_Optimizer')

		# Writing graph and other summaries in tensorflow.
		self.writer = tf.summary.FileWriter('training',self.sess.graph)
		init = tf.global_variables_initializer()
		self.sess.run(init)
				
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

		# Maintaining list of all goals and start locations. 
		self.goal_list = []
		self.start_list = []

	def save_model(self, model_index):
		if not(os.path.isdir("saved_models")):
			os.mkdir("saved_models")
		self.saver = tf.train.Saver(max_to_keep=None)			
		save_path = self.saver.save(self.sess,'saved_models/model_{0}.ckpt'.format(model_index))

	def initialize_tree(self):
		# Intialize the parse tree for this image.=
		self.state = parse_tree_node(label=0,x=0,y=0,w=self.image_size,h=self.image_size)
		self.current_parsing_index = 0
		self.parse_tree = [parse_tree_node()]
		self.parse_tree[self.current_parsing_index]=self.state

	def insert_node(self, state, index):	
		self.parse_tree.insert(index,state)

	def parse_nonterminal(self, image_index):
		rule_probabilities = self.sess.run(self.rule_probabilities,feed_dict={self.input: self.resized_image.reshape(1,self.image_size,self.image_size,1)})
	
		split_location = -1
		
		# Hard coding ban of splits for regions smaller than minimum width.		
		epislon = 1e-5
		rule_probabilities += epislon

		if (self.state.h<=self.minimum_width):
			rule_probabilities[0][[0,2]]=0.

		if (self.state.w<=self.minimum_width):
			rule_probabilities[0][[1,3]]=0.

		# Sampling a rule:
		rule_probabilities/=rule_probabilities.sum()

		if self.to_train:
			selected_rule = npy.random.choice(range(self.fcs1_output_shape),p=rule_probabilities[0])
		if not(self.to_train):
			selected_rule = npy.argmax(rule_probabilities[0])
			
		indices = self.map_rules_to_indices(selected_rule)

		# If it is a split rule:
		if selected_rule<=3:

			# Resampling until it gets a split INSIDE the segment. This just ensures the split lies within 0 and 1.
			if ((selected_rule==0) or (selected_rule==2)):
				counter = 0				

				# SAMPLING SPLIT LOCATION INSIDE THIS CONDITION:
				while (split_location<=0)or(split_location>=self.state.h):
					split_location = self.sess.run(self.sample_split, feed_dict={self.input: self.resized_image.reshape(1,self.image_size,self.image_size,1)})
					counter+=1

					split_copy = copy.deepcopy(split_location)
					# inter_split = split_location*self.state.h
					inter_split = split_location*self.imagey-self.state.y+self.ly

					if inter_split>(self.state.h/2):
						split_location = int(npy.floor(inter_split))
					else:
						split_location = int(npy.ceil(inter_split))

					# print("Y:",self.state.y,"H:",self.state.y,"Image Y:",self.imagey)
					# print("H SC:",split_copy,"SL:",split_location)

					if counter>25:
						print("State: H",self.state.h, "Split fraction:",split_copy, "Split location:",split_location)
			
				# Create splits.
				s1 = parse_tree_node(label=indices[0],x=self.state.x,y=self.state.y,w=self.state.w,h=split_location,backward_index=self.current_parsing_index)
				s2 = parse_tree_node(label=indices[1],x=self.state.x,y=self.state.y+split_location,w=self.state.w,h=self.state.h-split_location,backward_index=self.current_parsing_index)

			if ((selected_rule==1) or (selected_rule==3)):
				counter = 0

				# SAMPLING SPLIT LOCATION INSIDE THIS CONDITION:
				while (split_location<=0)or(split_location>=self.state.w):
					split_location = self.sess.run(self.sample_split, feed_dict={self.input: self.resized_image.reshape(1,self.image_size,self.image_size,1)})
					counter+=1
					
					split_copy = copy.deepcopy(split_location)
					# inter_split = split_location*self.state.w
					inter_split = split_location*self.imagex-self.state.x+self.lx
					
					# if inter_split>(self.image_size/2):
					if inter_split>(self.state.w/2):
						split_location = int(npy.floor(inter_split))
					else:
						split_location = int(npy.ceil(inter_split))
					
					# print("X:",self.state.x,"W",self.state.w,"Image X:",self.imagex)
					# print("W SC:",split_copy,"SL:",split_location)

					if counter>25:
						print("State: W",self.state.w, "Split fraction:",split_copy, "Split location:",split_location)

				# Create splits.
				s1 = parse_tree_node(label=indices[0],x=self.state.x,y=self.state.y,w=split_location,h=self.state.h,backward_index=self.current_parsing_index)
				s2 = parse_tree_node(label=indices[1],x=self.state.x+split_location,y=self.state.y,w=self.state.w-split_location,h=self.state.h,backward_index=self.current_parsing_index)
				
			# Update current parse tree with split location and rule applied.
			self.parse_tree[self.current_parsing_index].split = split_copy
			self.parse_tree[self.current_parsing_index].boundaryscaled_split = split_location
			self.parse_tree[self.current_parsing_index].rule_applied = selected_rule

			self.predicted_labels[image_index,s1.x:s1.x+s1.w,s1.y:s1.y+s1.h] = s1.label
			self.predicted_labels[image_index,s2.x:s2.x+s2.w,s2.y:s2.y+s2.h] = s2.label
			
			if (selected_rule<=1):
				# Insert splits into parse tree.
				self.insert_node(s1,self.current_parsing_index+1)
				self.insert_node(s2,self.current_parsing_index+2)

			if (selected_rule>=2):
				# Insert splits into parse tree.
				self.insert_node(s2,self.current_parsing_index+1)
				self.insert_node(s1,self.current_parsing_index+2)

			self.current_parsing_index+=1

		elif selected_rule>=4:
			# Now even with the different primitives we don't need more than 6 rules; since choice of primitive is independent of assignment of primitive.

			# Create a parse tree node object.
			s1 = copy.deepcopy(self.parse_tree[self.current_parsing_index])
			# Change label.
			s1.label=selected_rule-3
			# Change the backward index.
			s1.backward_index = self.current_parsing_index

			# Update current parse tree with rule applied.
			self.parse_tree[self.current_parsing_index].rule_applied = selected_rule

			# Insert node into parse tree.
			self.insert_node(s1,self.current_parsing_index+1)
			self.current_parsing_index+=1						
			self.predicted_labels[image_index,s1.x:s1.x+s1.w,s1.y:s1.y+s1.h] = s1.label

	def parse_primitive_terminal(self, image_index):
		# If primitive region: 
		if (self.state.label==1):

			primitive_probabilities = self.sess.run(self.primitive_probabilities, feed_dict={self.input: self.resized_image.reshape(1,self.image_size,self.image_size,1)})	

			if self.to_train:
				selected_primitive = npy.random.choice(range(self.number_primitives),p=primitive_probabilities[0])
			if not(self.to_train):
				selected_primitive = npy.argmax(primitive_probabilities[0])

			# For primitive 0, horizontal brush stroke from left to right. (at bottom)
			# For primitive 1, horizontal brush stroke from right to left. (at bottom)
			# For primitive 2, vertical brush stroke from top to bottom. (at left)
			# For primitive 3, vertical brush stroke from bottom to top. (at left)
			# print("Selected Primitive:",selected_primitive

			if (selected_primitive==0):
				self.current_start = npy.array([self.state.y+self.state.h/2,self.state.x])
				self.current_goal = npy.array([self.state.y+self.state.h/2,self.state.x+self.state.w])

				lower = max(self.state.y,self.state.y+(self.state.h-self.paintwidth)/2)
				upper = min(self.state.y+(self.state.h+self.paintwidth)/2,self.state.y+self.state.h)

				self.painted_image[self.state.x:(self.state.x+self.state.w), lower:upper] = 1.
				self.painted_images[image_index, self.state.x:(self.state.x+self.state.w), lower:upper] = 1.

			if (selected_primitive==1):
				self.current_start = npy.array([self.state.y+self.state.h/2,self.state.x+self.state.w])
				self.current_goal = npy.array([self.state.y+self.state.h/2,self.state.x])

				lower = max(self.state.y,self.state.y+(self.state.h-self.paintwidth)/2)
				upper = min(self.state.y+(self.state.h+self.paintwidth)/2,self.state.y+self.state.h)

				self.painted_image[self.state.x:(self.state.x+self.state.w), lower:upper] = 1.
				self.painted_images[image_index, self.state.x:(self.state.x+self.state.w), lower:upper] = 1.

			if (selected_primitive==2):
				self.current_start = npy.array([self.state.y,self.state.x+self.state.w/2])
				self.current_goal = npy.array([self.state.y+self.state.h,self.state.x+self.state.w/2])				

				lower = max(self.state.x,self.state.x+(self.state.w-self.paintwidth)/2)				
				upper = min(self.state.x+(self.state.w+self.paintwidth)/2,self.state.x+self.state.w)

				self.painted_image[lower:upper, self.state.y:self.state.y+self.state.h] = 1.
				self.painted_images[image_index,lower:upper, self.state.y:self.state.y+self.state.h] = 1.

			if (selected_primitive==3):
				self.current_start = npy.array([self.state.y+self.state.h,self.state.x+self.state.w/2])
				self.current_goal = npy.array([self.state.y,self.state.x+self.state.w/2])
				
				lower = max(self.state.x,self.state.x+(self.state.w-self.paintwidth)/2)				
				upper = min(self.state.x+(self.state.w+self.paintwidth)/2,self.state.x+self.state.w)

				self.painted_image[lower:upper, self.state.y:self.state.y+self.state.h] = 1.
				self.painted_images[image_index,lower:upper, self.state.y:self.state.y+self.state.h] = 1.

			self.previous_goal = copy.deepcopy(self.current_goal)

			self.start_list.append(self.current_start)
			self.goal_list.append(self.current_goal)

			self.parse_tree[self.current_parsing_index].primitive = selected_primitive

		self.state.reward = (self.true_labels[image_index, self.state.x:self.state.x+self.state.w, self.state.y:self.state.y+self.state.h]*self.painted_image[self.state.x:self.state.x+self.state.w, self.state.y:self.state.y+self.state.h]).sum()
		# self.state.reward += continuity_term*self.continuity_lambda	
		self.current_parsing_index+=1

	def propagate_rewards(self):

		# Traverse the tree in reverse order, accumulate rewards into parent nodes recursively as sum of rewards of children.
		# This is actually the return accumulated by any particular decision.
		# Now we are discounting based on the depth of the tree (not just sequence in episode)
		self.gamma = 0.98
		for j in reversed(range(len(self.parse_tree))):	
			if (self.parse_tree[j].backward_index>=0):
				self.parse_tree[self.parse_tree[j].backward_index].reward += self.parse_tree[j].reward*self.gamma

		for j in range(len(self.parse_tree)):
			self.parse_tree[j].reward /= (self.parse_tree[j].w*self.parse_tree[j].h)

		# Non-linearizing rewards.
		for j in range(len(self.parse_tree)):
			self.parse_tree[j].reward = npy.tan(self.parse_tree[j].reward)			

	def backprop(self, image_index):
		# Must decide whether to do this stochastically or in batches. # For now, do it stochastically, moving forwards through the tree.
		for j in range(len(self.parse_tree)):
			self.state = self.parse_tree[j]
			
			boundary_width = 2
			lowerx = max(0,self.state.x-boundary_width)
			upperx = min(self.image_size,self.state.x+self.state.w+boundary_width)
			lowery = max(0,self.state.y-boundary_width)
			uppery = min(self.image_size,self.state.y+self.state.h+boundary_width)

			self.image_input = self.images[image_index, lowerx:upperx, lowery:uppery]
			self.resized_image = cv2.resize(self.image_input,(self.image_size,self.image_size))

			rule_weight = 0
			split_weight = 0
			primitive_weight = 0
			target_rule = npy.zeros(self.fcs1_output_shape)
			target_primitive = npy.zeros(self.number_primitives)

			if self.parse_tree[j].label==0:
				rule_weight = self.parse_tree[j].reward
				target_rule[self.parse_tree[j].rule_applied] = 1.
				if self.parse_tree[j].rule_applied<=3:
					split_weight = self.parse_tree[j].reward

			if self.parse_tree[j].label==1:
				primitive_weight = self.parse_tree[j].reward
				target_primitive[self.parse_tree[j].primitive] = 1.				

			self.sess.run(self.train, feed_dict={self.input: self.resized_image.reshape(1,self.image_size,self.image_size,1), \
				self.sampled_split: self.parse_tree[j].split, self.rule_return_weight: rule_weight, self.split_return_weight: split_weight, self.target_rule: target_rule, \
					self.primitive_return_weight: primitive_weight, self.target_primitive: target_primitive})

	def construct_parse_tree(self,image_index):
		# WHILE WE TERMINATE THAT PARSE:

		self.painted_image = -npy.ones((self.image_size,self.image_size))
		self.alternate_painted_image = -npy.ones((self.image_size,self.image_size))
		self.alternate_predicted_labels = npy.zeros((self.image_size,self.image_size))
		
		while ((self.predicted_labels[image_index]==0).any() or (self.current_parsing_index<=len(self.parse_tree)-1)):
	
			# Forward pass of the rule policy- basically picking which rule.
			self.state = self.parse_tree[self.current_parsing_index]
			# Pick up correct portion of image.
			boundary_width = 2
			lowerx = max(0,self.state.x-boundary_width)
			upperx = min(self.image_size,self.state.x+self.state.w+boundary_width)
			lowery = max(0,self.state.y-boundary_width)
			uppery = min(self.image_size,self.state.y+self.state.h+boundary_width)

			self.image_input = self.images[image_index, lowerx:upperx, lowery:uppery]

			self.imagex = upperx-lowerx
			self.imagey = uppery-lowery
			self.ux = upperx
			self.uy = uppery
			self.lx = lowerx
			self.ly = lowery

			self.resized_image = cv2.resize(self.image_input,(self.image_size,self.image_size))

			# If the current non-terminal is a shape.
			if (self.state.label==0):
				# print("PARSING NON TERMINAL")
				self.parse_nonterminal(image_index)

			# If the current non-terminal is a region assigned a particular primitive.
			if (self.state.label==1) or (self.state.label==2):
				self.parse_primitive_terminal(image_index)
			
			self.update_plot_data(image_index)
			# self.fig.savefig("Image_{0}_Step_{1}.png".format(image_index,self.current_parsing_index),format='png',bbox_inches='tight')

	def attention_plots(self):

		self.mask = -npy.ones((self.image_size,self.image_size))
		self.display_discount = 0.8
		self.backward_discount = 0.98

		for j in range(self.current_parsing_index):
			self.dummy_state = self.parse_tree[j]
		 	self.mask[self.dummy_state.x:self.dummy_state.x+self.dummy_state.w,self.dummy_state.y:self.dummy_state.y+self.dummy_state.h] = -(self.backward_discount**j)
		
		for j in range(self.current_parsing_index,len(self.parse_tree)):
			self.dummy_state = self.parse_tree[j]
			self.mask[self.dummy_state.x:self.dummy_state.x+self.dummy_state.w,self.dummy_state.y:self.dummy_state.y+self.dummy_state.h] = (self.display_discount**(j-self.current_parsing_index))

	def update_plot_data(self, image_index):
	
		# if (self.predicted_labels[image_index]==1).any():
		# self.alternate_painted_image[npy.where(self.predicted_labels[image_index]==1)]=1.
		self.alternate_painted_image[npy.where(self.painted_images[image_index]==1)]=1.
		self.alternate_predicted_labels[npy.where(self.predicted_labels[image_index]==1)]=1.
		self.alternate_predicted_labels[npy.where(self.predicted_labels[image_index]==2)]=-1.

		if self.plot:
			self.fig.suptitle("Processing Image: {0}".format(image_index))
			self.sc1.set_data(self.alternate_predicted_labels)
			self.attention_plots()
			self.sc2.set_data(self.mask)

			# npy.save("Mask_{0}.npy".format(image_index),self.mask)
			self.sc3.set_data(self.images[image_index])
			self.sc4.set_data(self.alternate_painted_image)

			# Plotting split line segments from the parse tree.
			split_segs = []
			for j in range(len(self.parse_tree)):

				colors = ['r']

				if self.parse_tree[j].label==0:
					if (self.parse_tree[j].rule_applied==1) or (self.parse_tree[j].rule_applied==3):
						
						# sc = self.parse_tree[j].split*self.parse_tree[j].w
						# if sc>(self.parse_tree[j].w/2):
						# 	sc = int(npy.floor(sc))
						# else:
						# 	sc = int(npy.ceil(sc))
						sc = self.parse_tree[j].boundaryscaled_split
						# split_segs.append([[self.parse_tree[j].x+sc,self.parse_tree[j].y],[self.parse_tree[j].x+sc,self.parse_tree[j].y+self.parse_tree[j].h]])								
						split_segs.append([[self.parse_tree[j].y,self.parse_tree[j].x+sc],[self.parse_tree[j].y+self.parse_tree[j].h,self.parse_tree[j].x+sc]])
						
					if (self.parse_tree[j].rule_applied==0) or (self.parse_tree[j].rule_applied==2):
						
						# sc = self.parse_tree[j].split*self.parse_tree[j].h					

						# if sc>(self.parse_tree[j].h/2):
						# 	sc = int(npy.floor(sc))
						# else:
						# 	sc = int(npy.ceil(sc))
						sc = self.parse_tree[j].boundaryscaled_split
						# split_segs.append([[self.parse_tree[j].x,self.parse_tree[j].y+sc],[self.parse_tree[j].x+self.parse_tree[j].w,self.parse_tree[j].y+sc]])															
						split_segs.append([[self.parse_tree[j].y+sc,self.parse_tree[j].x],[self.parse_tree[j].y+sc,self.parse_tree[j].x+self.parse_tree[j].w]])

				# print(split_segs)	
			split_lines = LineCollection(split_segs, colors='k', linewidths=2)
			split_lines2 = LineCollection(split_segs, colors='k',linewidths=2)
			split_lines3 = LineCollection(split_segs, colors='k', linewidths=2)

			self.split_lines = self.ax[3].add_collection(split_lines)				
			self.split_lines2 = self.ax[1].add_collection(split_lines2)
			self.split_lines3 = self.ax[2].add_collection(split_lines3)


			if len(self.start_list)>0 and len(self.goal_list)>0:
				segs = [[npy.array([0,0]),self.start_list[0]]]
				color_index = ['k']
				linewidths = [1]

				for i in range(len(self.goal_list)-1):
					segs.append([self.start_list[i],self.goal_list[i]])
					# Paint
					color_index.append('y')
					linewidths.append(5)
					segs.append([self.goal_list[i],self.start_list[i+1]])
					# Don't paint.
					color_index.append('k')
					linewidths.append(1)
				# Add final segment.
				segs.append([self.start_list[-1],self.goal_list[-1]])
				color_index.append('y')
				linewidths.append(5)

				lines = LineCollection(segs, colors=color_index,linewidths=linewidths)
				self.lines = self.ax[0].add_collection(lines)

				self.fig.canvas.draw()
				raw_input("Press any key to continue.")
				plt.pause(0.1)	
				del self.ax[0].collections[-1]

			del self.ax[3].collections[-1]
			del self.ax[2].collections[-1]
			del self.ax[1].collections[-1]

	def define_plots(self):
		image_index = 0
		if self.plot:
			# self.fig, self.ax = plt.subplots(1,4,sharey=True)
			self.fig, self.ax = plt.subplots(1,4)
			self.fig.show()
			
			self.sc1 = self.ax[0].imshow(self.predicted_labels[image_index],aspect='equal',cmap='jet',extent=[0,self.image_size,0,self.image_size],origin='lower')
			# self.sc1 = self.ax[0].imshow(self.predicted_labels[image_index],aspect='equal',cmap='jet')
			self.sc1.set_clim([-1,1])
			# self.sc1.set_clim([0,2])
			self.ax[0].set_title("Predicted Labels")
			self.ax[0].set_adjustable('box-forced')
			# self.ax[0].set_xlim(self.ax[0].get_xlim()[0]-0.5, self.ax[0].get_xlim()[1]+0.5) 
			# self.ax[0].set_ylim(self.ax[0].get_ylim()[0]-0.5, self.ax[0].get_ylim()[1]+0.5) 

			self.sc2 = self.ax[1].imshow(self.true_labels[image_index],aspect='equal',cmap='jet',extent=[0,self.image_size,0,self.image_size],origin='lower')
			# self.sc2 = self.ax[1].imshow(self.true_labels[image_index],aspect='equal',cmap='jet')
			self.sc2.set_clim([-1,1])
			self.ax[1].set_title("Parse Tree")
			self.ax[1].set_adjustable('box-forced')

			self.sc3 = self.ax[2].imshow(self.images[image_index],aspect='equal',cmap='jet',extent=[0,self.image_size,0,self.image_size],origin='lower')
			# self.sc3 = self.ax[2].imshow(self.images[image_index],aspect='equal',cmap='jet')
			# self.sc3 = self.ax[2].imshow(self.images[image_index],aspect='equal',cmap='jet',origin='lower')
			# self.sc3 = self.ax[2].imshow(self.images[image_index],aspect='equal',cmap='jet',extent=[0,self.image_size,+1,self.image_size+1],origin='lower')
			self.sc3.set_clim([-1,1.2])
			self.ax[2].set_title("Actual Image")
			# self.ax[2].plot([20,20,30,30],[10,40,10,40])
			self.ax[2].set_adjustable('box-forced')

			self.sc4 = self.ax[3].imshow(self.true_labels[image_index],aspect='equal',cmap='jet',extent=[0,self.image_size,0,self.image_size],origin='lower')
			# self.sc4 = self.ax[3].imshow(self.true_labels[image_index],aspect='equal',cmap='jet') #, extent=[0,self.image_size,0,self.image_size],origin='lower')
			self.sc4.set_clim([-1,1])
			self.ax[3].set_title("Segmented Painted Image")
			self.ax[3].set_adjustable('box-forced')			

			self.fig.canvas.draw()
			# manager = plt.get_current_fig_manager()
			# manager.resize(*manager.window.maxsize())	
			plt.pause(0.1)	
	
	def meta_training(self,train=True):

		image_index = 0
		self.painted_image = -npy.ones((self.image_size,self.image_size))

		self.define_plots()
		self.to_train = train
		# For all epochs
		if not(train):
			self.num_epochs=1

		# For all epochs
		for e in range(self.num_epochs):
			for i in range(self.num_images):

				self.initialize_tree()
				self.construct_parse_tree(i)
				# self.compute_rewards(i)
				self.propagate_rewards()
				print("#___________________________________________________________________________")
				print("Epoch:",e,"Training Image:",i,"TOTAL REWARD:",self.parse_tree[0].reward)

				if train:
					self.backprop(i)

				self.start_list = []
				self.goal_list = []
				
			if train:
				npy.save("parsed_{0}.npy".format(e),self.predicted_labels)
				npy.save("painted_images_{0}.npy".format(e),self.painted_images)
				self.save_model(e)
			else: 
				npy.save("validation_1.npy".format(e),self.predicted_labels)
				npy.save("valid_painting_1.npy",self.painted_images)
				
			self.predicted_labels = npy.zeros((self.num_images,self.image_size,self.image_size))
			self.painted_images = -npy.ones((self.num_images, self.image_size,self.image_size))

	############################
	# Pixel labels: 
	# 0 for shape
	# 1 for shape with primitive 1
	# 2 for region with no primitive (not to be painted)
	############################

	def map_rules_to_indices(self, rule_index):
		if (rule_index<=3):
			return [0,0]
		if (rule_index==4):
			return 1
		if (rule_index==5):
			return 2

	############################
	# Rule numbers:
	# 0 (Shape) -> (Shape)(Shape) 								(Vertical split)
	# 1 (Shape) -> (Shape)(Shape) 								(Horizontal split)
	# 2 (Shape) -> (Shape)(Shape) 								(Vertical split with opposite order: top-bottom expansion)
	# 3 (Shape) -> (Shape)(Shape) 								(Horizontal split with opposite order: right-left expansion)
	# 4 (Shape) -> (Region with primitive #) 
	# 5 (Shape) -> (Region not to be painted)
	############################

	def preprocess_images_labels(self):

		noise = 0.2*npy.random.rand(self.num_images,self.image_size,self.image_size)
		self.images[npy.where(self.images==2)]=-1
		self.true_labels[npy.where(self.true_labels==2)]=-1
		self.images += noise

def main(args):

	# # Create a TensorFlow session with limits on GPU usage.
	# gpu_ops = tf.GPUOptions(allow_growth=True,visible_device_list="1,2")
	gpu_ops = tf.GPUOptions(allow_growth=True,visible_device_list="3,1")
	config = tf.ConfigProto(gpu_options=gpu_ops)
	sess = tf.Session(config=config)

	hierarchical_model = hierarchical()
	# hierarchical_model.initialize_tensorflow_model(sess)
	
	# MUST LOAD IMAGES / LOAD NOISY IMAGES (So that the CNN has some features to latch on to.)	
	hierarchical_model.images = npy.load(str(sys.argv[1]))	
	hierarchical_model.true_labels = npy.load(str(sys.argv[2]))
	
	hierarchical_model.preprocess_images_labels()
	hierarchical_model.plot = 0
	
	load = 1
	if load:
		model_file = str(sys.argv[5])
		hierarchical_model.initialize_tensorflow_model(sess,model_file)
	else:
		hierarchical_model.initialize_tensorflow_model(sess)

	# CALL TRAINING
	hierarchical_model.meta_training(train=False)
	# hierarchical_model.meta_training(train=True)

if __name__ == '__main__':
	main(sys.argv)