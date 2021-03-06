import flask
import zeeguu_core
from zeeguu_core.content_recommender.mixed_recommender import article_recommendations_for_user, cohort_articles_for_user
from zeeguu_core.model import UserArticle, UserReadingSession, User

from .utils.route_wrappers import cross_domain, with_session
from .utils.json_result import json_result
from . import api

session = zeeguu_core.db.session


# ---------------------------------------------------------------------------
@api.route("/user_articles/recommended", methods=("GET",))
@api.route("/user_articles/recommended/<int:count>", methods=("GET",))
# ---------------------------------------------------------------------------
@cross_domain
@with_session
def user_articles_recommended(count: int = 20):
    """
        recommendations for all languages
    """

    return json_result(article_recommendations_for_user(flask.g.user, count))


# ---------------------------------------------------------------------------
@api.route("/user_articles/starred_or_liked", methods=("GET",))
# ---------------------------------------------------------------------------
@cross_domain
@with_session
def user_articles_starred_and_liked():
    return json_result(UserArticle.all_starred_and_liked_articles_of_user_info(flask.g.user))


# ---------------------------------------------------------------------------
@api.route("/cohort_articles", methods=("GET",))
# ---------------------------------------------------------------------------
@cross_domain
@with_session
def user_articles_cohort():
    """
        get all articles for the cohort associated with the user
    """

    return json_result(cohort_articles_for_user(flask.g.user))


# ---------------------------------------------------------------------------
@api.route("/user_article_history/<user_id>", methods=("GET",))
# ---------------------------------------------------------------------------
@cross_domain
# @with_session
def user_article_history(user_id):
    user = User.find_by_id(user_id)

    sessions = UserReadingSession.find_by_user(user.id)

    dates = {}
    for each in sessions[:-650:-1]:
        if each.article and each.duration > 1000:
            if not dates.get(each.human_readable_date()):
                dates[each.human_readable_date()] = []

            # user_article = UserArticle.find(user, each.article)
            events_in_this_session = each.events_in_this_session()

            has_like = False
            feedback = ""
            difficulty = ""
            for event in events_in_this_session:
                if event.is_like():
                    has_like = True
                if event.is_feedback():
                    feedback = event.value
                    difficulty = "fk: " + str(each.article.fk_difficulty)

            dates[each.human_readable_date()].append(
                {
                    'date': each.human_readable_date(),
                    'duration': each.human_readable_duration(),
                    'start': each.start_time.strftime("%H:%M:%S"),
                    'article': each.article.title,
                    'liked': has_like,
                    'feedback': feedback,
                    'difficulty': difficulty
                }
            )

    text_result = f"<title>{user.name}</title>"
    text_result += f"<h1>{user.name} ({user.id})</h1><br/>"
    previous_title = ""
    for date in dates:
        text_result += date + "<br/>"
        for session in dates[date]:
            if previous_title != session['article']:
                text_result += f"<br/>&nbsp;&nbsp;<b> {session['article']} </b><br/>"
            text_result += f"&nbsp;&nbsp;&nbsp;&nbsp; {session['duration']} ({session['start']})"
            if session['liked']:
                text_result += ' (LIKED) '
            text_result += session['difficulty'] + " " + session['feedback'] + " <br/>"
            previous_title = session['article']

        text_result += "<br/><br/>"

    return text_result
