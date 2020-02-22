from flask import Blueprint, render_template

errors = Blueprint("errors", __name__)


@errors.app_errorhandler(404) # @errors.errorhandler also exists but it only handles error for a particular Blueprint, while app_errorhandler(404) handles error for whole app
def error_404(error):
    return render_template("errors/404.html"), 404 # flask can return the status code together for a route, but default is 200. That is why we did not specify for the other routes

@errors.app_errorhandler(403)
def error_403(error):
    return render_template("errors/403.html"), 403

@errors.app_errorhandler(500)
def error_500(error):
    return render_template("errors/500.html"), 500