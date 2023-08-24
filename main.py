from flask import Flask, render_template, redirect, url_for, request
from flask_bootstrap import Bootstrap5
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired
import requests
from sqlalchemy import func


MOVIE_DB_API_KEY = "419b7ca091f2cc50fc762108adad02ce"
movie_endpoint = "https://api.themoviedb.org/3/search/movie"
MOVIE_DB_INFO_URL = "https://api.themoviedb.org/3/movie"
MOVIE_DB_IMAGE_URL = "https://image.tmdb.org/t/p/w500"
app = Flask(__name__)
app.config['SECRET_KEY'] = '8BYkEfBA6O6donzWlSihBXox7C0sKR6b'
Bootstrap5(app)

##CREATE DB
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///movies.db'
db = SQLAlchemy()
db.init_app(app)


class Movie(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(250), unique=True, nullable=False)
    year = db.Column(db.Integer, nullable=False)
    description = db.Column(db.String(500), nullable=False)
    rating = db.Column(db.Float, nullable=True)
    ranking = db.Column(db.Integer, nullable=True)
    review = db.Column(db.String(250), nullable=True)
    img_url = db.Column(db.String(250), nullable=False)
    reversed_rating = -1*rating

with app.app_context():
    db.create_all()

class RateMovieForm(FlaskForm):
    rating = StringField("Your Rating Out of 10 e.g. 7.5")
    review = StringField("Your Review")
    submit = SubmitField("Done")

class AddMovieForm(FlaskForm):
    title = StringField("Movie Title")
    submit = SubmitField("Add Movie")


@app.route("/")
def home():
    result = db.session.execute(db.select(Movie).order_by(Movie.reversed_rating))
    all_movies = list(result.scalars())
    for movie in all_movies:
        movie.ranking = all_movies.index(movie)+1
    return render_template("index.html", movies=all_movies)


@app.route("/edit", methods=["GET", "POST"])
def rate_movie():
    form = RateMovieForm()
    movie_id = request.args.get("id")
    movie = db.get_or_404(Movie, movie_id)
    if form.validate_on_submit():
        movie.rating = float(form.rating.data)
        movie.review = form.review.data
        db.session.commit()
        return redirect(url_for('home'))
    return render_template("edit.html", movie=movie, form=form)


@app.route('/delete/<int:id>')
def delete(id):
    delete_movie = db.get_or_404(Movie, id)
    db.session.delete(delete_movie)
    db.session.commit()
    return redirect(url_for("home"))




@app.route('/add', methods=["GET", "POST"])
def add_movie():
    form = AddMovieForm()
    if form.validate_on_submit():
        movie_to_search = str(form.title.data).replace(" ", "+")
        params = {
            "query": movie_to_search,
            "api_key": MOVIE_DB_API_KEY
        }
        data = requests.get(url=movie_endpoint, params=params).json()
        number_of_results = len(data["results"])
        movie_titles = []
        movie_dates = []
        movie_ids= []
        for i in range(number_of_results):
            title = data["results"][i]["original_title"]
            date = data["results"][i]["release_date"]
            id = data["results"][i]["id"]
            movie_titles.append(title)
            movie_dates.append(date)
            movie_ids.append(id)
        return render_template("select.html", movie_titles=movie_titles, movie_dates=movie_dates, movie_ids=movie_ids)
    return render_template("add.html", form=form)



@app.route("/find")
def find_movie():
    movie_api_id = request.args.get("id")
    rows = db.session.query(func.count(Movie.id)).scalar()
    if movie_api_id:
        movie_api_url = f"{MOVIE_DB_INFO_URL}/{movie_api_id}"
        response = requests.get(movie_api_url, params={"api_key": MOVIE_DB_API_KEY, "language": "en-US"})
        data = response.json()
        new_movie = Movie(
            id=rows+1,
            title=data["title"],
            year=data["release_date"].split("-")[0],
            img_url=f"{MOVIE_DB_IMAGE_URL}{data['poster_path']}",
            description=data["overview"]
        )
        db.session.add(new_movie)
        db.session.commit()
        return redirect(url_for("rate_movie", id=new_movie.id))


if __name__ == '__main__':
    app.run(debug=True, port=5003)