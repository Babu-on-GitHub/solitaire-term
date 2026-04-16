import sys

from solitaire.ui.app import SolitaireApp


def main() -> None:
    debug = "--debug" in sys.argv
    app = SolitaireApp()
    if debug:
        app.engine.debug_near_win()
    app.run()


if __name__ == "__main__":
    main()
