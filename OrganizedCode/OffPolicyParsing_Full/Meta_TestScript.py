#!/usr/bin/env python
from headers import *

# for i in range(0,260,10):
for i in range(0,260,10):
	print("STARTING WITH:",i)
	# command = "python ../Meta_RLClass.py --images ../../../ImageSets/NEWSTRIPS.npy --labels ../../../ImageSets/NEWSTRIPS.npy --train 0 --gpu 0,1 --tanrewards 0 --likelihoodratio 0 --model saved_models/model_epoch{0}.ckpt".format(i)
	# command = "python ../Meta_RLClass.py --images ../../../ImageSets/NEWSTRIPS.npy --labels ../../../ImageSets/NEWSTRIPS.npy --train 0 --gpu 0,1 --tanrewards 0 --likelihoodratio 0 --suffix model_k2_{0} --model saved_models/model_epoch{0}.ckpt".format(i)
	# command = "python ../Meta_RLClass.py --images ../../../ImageSets/FAKE_IMAGES.npy --labels ../../../ImageSets/FAKE_IMAGES.npy --train 0 --gpu 0,1 --tanrewards 0 --likelihoodratio 0 --model saved_models/model_epoch{0}.ckpt --suffix model_k2_{0}".format(i)

	command = "python ../Meta_RLClass.py --images ../../../ImageSets/NEWSTRIPS.npy --labels ../../../ImageSets/NEWSTRIPS.npy --train 0 --gpu 0,1 --tanrewards 0 --likelihoodratio 0 --model saved_models/model_epoch{0}.ckpt --suffix model_consteps_k5_{0} --infogain 0".format(i)
	subprocess.call(command.split(),shell=False)
