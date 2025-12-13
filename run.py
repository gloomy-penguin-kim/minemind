import logging 

logging.basicConfig(level=logging.ERROR,
                    format='%(asctime)s - %(levelname)s - %(filename)s:%(lineno)d - %(funcName)s - %(message)s')

from minemind.cli import main
main()

if __name__ == "__main__":
    main()