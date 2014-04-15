version:
	git describe --tags > version.txt
	perl -p -i -e 's/-/./g' version.txt

sdist: version
	python setup.py sdist

signed-rpm: sdist
	rpmbuild -ba python-psphere.spec --sign --define "_sourcedir `pwd`/dist"

rpm: sdist
	rpmbuild -ba python-psphere.spec --define "_sourcedir `pwd`/dist"

srpm: sdist
	rpmbuild -bs python-psphere.spec --define "_sourcedir `pwd`/dist"

pylint:
	pylint --rcfile=pylint.conf imagefactory imgfac

unittests:
	python -m unittest discover -v

clean:
	rm -rf MANIFEST build dist python-psphere.spec version.txt
