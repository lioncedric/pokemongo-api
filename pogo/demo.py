#!/usr/bin/python
import argparse
import logging
import time
import sys

import api
import location

def setupLogger():
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    ch = logging.StreamHandler()
    ch.setLevel(logging.DEBUG)
    formatter = logging.Formatter('Line %(lineno)d,%(filename)s  - %(asctime)s - %(levelname)s - %(message)s')
    ch.setFormatter(formatter)
    logger.addHandler(ch)


if __name__ == '__main__':
    setupLogger()
    logging.debug('Logger set up')

    parser = argparse.ArgumentParser()
    parser.add_argument("-a", "--auth", help="Auth Service",
        required=True)
    parser.add_argument("-u", "--username", help="Username", required=True)
    parser.add_argument("-p", "--password", help="Password", required=True)
    parser.add_argument("-l", "--location", help="Location", required=True)
    parser.add_argument("-s", "--client_secret", help="PTC Client Secret")
    args = parser.parse_args()

    if args.auth not in ['ptc', 'google']:
        logging.error('Invalid auth service {}'.format(args.auth))
        sys.exit(-1)

    if args.auth == 'ptc':
        session = api.createPTCSession(args.username, args.password, args.location)
    elif args.auth == 'google':
        session = api.createGoogleSession(args.username, args.password, args.location)

    if session: # do stuff

        # Get profile        
        logging.info("Printing Profile:")
        profile = session.getProfile()
        logging.info(profile)

        # Get Map details
        logging.info("Printing Nearby Pokemon:")
        cells = session.getMapObjects()
        closest = float("Inf")
        pokemonBest = None
        latitude, longitude, _ = session.getLocation()
        for cell in cells.map_cells:
            for pokemon in cell.wild_pokemons:
                logging.info("%i at %f,%f"%(pokemon.pokemon_data.pokemon_id,pokemon.latitude,pokemon.longitude))
                dist = location.getDistance(latitude, longitude, pokemon.latitude, pokemon.longitude)
                if dist < closest:
                    pokemonBest = pokemon

        if pokemonBest:
            logging.info("Catching nearest pokemon:")
            session.walkTo(pokemonBest.latitude, pokemonBest.longitude)
            logging.info(session.encounterAndCatch(pokemonBest))

        # Do Inventory stuff
        logging.info("Get Inventory")
        logging.info(session.getInventory())

        # Find nearest fort (pokestop)
        logging.info("Spinnning Nearest Fort")
        closest = float("Inf")
        fortBest = None
        latitude, longitude, _ = session.getLocation()

        ordered_forts = []

        for cell in cells.map_cells:
            for fort in cell.forts:
                dist = location.getDistance(latitude, longitude, fort.latitude, fort.longitude)
                if fort.type == 1:
                    ordered_forts.append({'distance': dist, 'fort': fort})

        ordered_forts = sorted(ordered_forts, key=lambda k: k['distance'])

        logging.info("Get Inventory")
        print(session.getInventory())

        for ordered_fort in ordered_forts:
            dist = ordered_fort['distance']
            fort = ordered_fort['fort']
            closest = dist
            # No fort, demo == over
            if fort:
                # Walk over to said fort
                epsilon = 0.0001
                step = 0.000010
                vector = [(fort.latitude - latitude)/closest, (fort.longitude - longitude)/closest]
                dist = closest
                while dist > epsilon:
                    logging.info("%f units -> %f units away" % (dist, epsilon))
                    latitude += vector[0] * step
                    longitude += vector[1] * step
                    session.setCoords(latitude, longitude)
                    dist = math.hypot((fort.latitude - latitude), (fort.longitude - longitude))
                    time.sleep(1)

            # Give it a spin
            fortResponse = session.getFortSearch(fortBest)
            logging.info(fortResponse)

    else:
        logging.critical('Session not created successfully')