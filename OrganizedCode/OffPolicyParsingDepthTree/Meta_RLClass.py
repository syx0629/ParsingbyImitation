#!/usr/bin/env python
from headers import *
import TF_Model
import Data_Loader
import OffPolicyParser
import Memory

class Meta_RLClass():

	def __init__(self, session=None,arguments=None):

		self.sess = session
		self.args = arguments
		self.batch_size = 5
		self.num_epochs = 250
		self.save_every = 1

		# Instantiate data loader class to load and preprocess the data.
		self.data_loader = Data_Loader.DataLoader(image_path=self.args.images,label_path=self.args.labels)
		self.data_loader.preprocess()
		
		# # Instantiate Model Class.		
		self.model = TF_Model.Model(num_channels=self.data_loader.num_channels)		
		self.args.train = bool(self.args.train)

		if self.args.model:
			self.model.create_network(self.sess,pretrained_weight_file=self.args.model,to_train=self.args.train)
		else:
			self.model.create_network(self.sess,to_train=self.args.train)

		# Instantiate memory. 
		self.memory = Memory.Replay_Memory()

		# Instantiate parser, passing arguments to take care of train / test / IGM within the parsing code. 
		self.parser = OffPolicyParser.Parser(self.model,self.data_loader,self.memory,self.args,self.sess)
		
	def train(self):
		self.parser.meta_training(self.args.train)

def parse_arguments():
	parser = argparse.ArgumentParser(description='Primitive-Aware Segmentation Argument Parsing')
	parser.add_argument('--images',dest='images',type=str)
	parser.add_argument('--labels',dest='labels',type=str)
	parser.add_argument('--suffix',dest='suffix',type=str)
	parser.add_argument('--gpu',dest='gpu')
	parser.add_argument('--train',dest='train',type=int,default=1)
	parser.add_argument('--depth_terminate',dest='depth_terminate',type=int,default=0)
	parser.add_argument('--infogain',dest='igm',type=int,default=0)
	parser.add_argument('--model',dest='model',type=str)
	return parser.parse_args()

def main(args):

	args = parse_arguments()

	# # Create a TensorFlow session with limits on GPU usage.
	gpu_ops = tf.GPUOptions(allow_growth=True,visible_device_list=args.gpu)
	config = tf.ConfigProto(gpu_options=gpu_ops)
	sess = tf.Session(config=config)

	hierarchical_model = Meta_RLClass(session=sess,arguments=args)
	hierarchical_model.train()

if __name__ == '__main__':
	main(sys.argv)


