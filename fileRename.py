import os


def main():

	folder = "dataset-part1"
	for count, filename in enumerate(os.listdir(folder)):
		dst = f"{str(count)}.jpg"
		# foldername/filename, if .py file is outside folder
		src = f"{folder}/{filename}"
		dst = f"{folder}/{dst}"

		# rename() function will
		# rename all the files
		os.rename(src, dst)


# Driver Code
if __name__ == '__main__':

	# Calling main() function
	main()
