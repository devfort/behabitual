coverage:
	coverage run --branch manage.py test
	coverage html --omit='/home/vagrant/.virtualenvs/*,*/admin.py,*/migrations/*'
	@echo "And look at htmlcov/index.html in some sort of HTML-based device."

more_coverage:
	@coverage report --fail-under=100 --omit='/home/vagrant/.virtualenvs/*,*/admin.py,*/migrations/*' >/dev/null || echo "You need more tests. Write more tests."
