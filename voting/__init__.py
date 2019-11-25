from collections import defaultdict
import json
import logging

from jose import (
    jwk,
    jwt,
)
import tornado.ioloop
from tornado.web import (
    Application,
    HTTPError,
    RequestHandler,
)


logger = logging.getLogger()
logger.setLevel("DEBUG")


with open("./data/iam-prod-keys.json") as kf:
    KEYS = json.load(kf)
ISSUER = "https://iam.humanbrainproject.eu/auth/realms/hbp"


def bearer_authtenticated(fn: callable) -> callable:
    def wrapped(self: RequestHandler, *args, **kwargs):
        bearer = self.request.headers["authorization"].split(" ")[1]
        payload = jwt.decode(
            bearer,
            KEYS,
            algorithms=["RS256"],
            issuer=ISSUER,
            options={"verify_aud": False},
        )
        user = payload["preferred_username"]
        return fn(self, user, *args, **kwargs)

    return wrapped


class InvalidVoteException(Exception):
    pass


class VotesHandler(RequestHandler):
    _options = ['A', 'B', 'C']

    @bearer_authtenticated
    def get(self, user: str) -> None:
        self.write({'vote': self.application.context['votes'][user]})

    @bearer_authtenticated
    def post(self, user: str) -> None:
        logging.info("Posting vote")
        try:
            vote = json.loads(self.request.body)['vote']
            self._validate(vote)
        except KeyError:
            self.write({"Error": f"Vote is required."})
            raise HTTPError(400, "Invalid option for vote.")
        except InvalidVoteException:
            self.write({"Error": f"Vote should be one of {self._options}"})
            raise HTTPError(400, "Invalid option for vote.")
        except json.JSONDecodeError:
            self.write({"error": "Invalid JSON"})
            raise HTTPError(400, "Invalid json")
        old = self.application.context['votes'][user]
        if old and not (old == vote):
            self.application.context['tally'][old] -= 1
        changed = not old == vote
        if changed:
            self.application.context['tally'][vote] += 1
            self.application.context['votes'][user] = vote
        logging.info(f"voted for: {vote}, new: {not old}, changed: {changed}")
        self.write(f"hello {user}")

    def _validate(self, vote):
        if vote not in self._options:
            raise InvalidVoteException


class ResultsHandler(RequestHandler):
    def get(self):
        self.write(self.application.context['tally'])


def main():
    import os
    try:
        port = int(os.environ.get('SVC_PORT'), 8080)
    except Exception:
        port = 8080
    app = Application([
        ("/votes", VotesHandler),
        ("/results", ResultsHandler),
    ])
    app.context = {
        "votes": defaultdict(lambda: None),
        "version": 0,
        "tally": defaultdict(int),
    }
    app.listen(port)
    tornado.ioloop.IOLoop.current().start()


if __name__ == "__main__":
    main()
