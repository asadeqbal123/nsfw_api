from nudenet import NudeClassifier

# initialize classifier (downloads the checkpoint file automatically the first time)
classifier = NudeClassifier()

# Classify single image
print(classifier.classify(r"C:\Users\eqbal\Downloads\wmnamgcqzf4snbiawnzk.jpg"))