import httpx
import asyncio
import json


class Router:
    """Main router class

    Attributes:
        TEST_MQ_API_KEY (str): An API key used for testing, it's not guaranteed         that it will work. DON'T USE IN PRODUCTION!
        TEST_ADDRESS_LIST (list of str): List of addresses for testing purposes. DON'T USE IN PRODUCTION!
    """

    TEST_MQ_API_KEY = 'nrXeeq9i2Hv2pcSIkAEyuEUrvmlT7PIa'

    TEST_ADDRESS_LIST = [
        'Av Hermann August Lepper 10 Joinville Brasil',
        'Rua Pastor Guilherme Rau 462 Joinville Brasil',
        'Rua Xanxere 60 Joinville Brasil',
        'Rua Max Colin 941 Joinville Brasil',
        'Rua Max Lepper 156 Joinville Brasil',
        'Rua Paulo Malschitzki 200 Joinville Brasil'
    ]

    def __init__(self, map_quest_api_key=TEST_MQ_API_KEY):
        """
        Router class constructor.

        Attributes:
            map_quest_api_key (str): Your API key to use MapQuest API.
        """
        self.map_quest_api_key = map_quest_api_key

    def get_route(self, address_list=TEST_ADDRESS_LIST):
        """
        Main method that receives a list of addresses, calls the necessary APIs
        and outputs the ordered optimal route.

        Args:
            address_list (list of str): the list of addresses that will be
                used to generate the optimal route.
                ATTENTION: Departure and arrival addresses must be the first and last elements in the list respectively.

        Returns:
            list of str: Ordered addresses for optimal route.
        """

        # Check if address_list argument is in fact a list
        if not isinstance(address_list, list):
            raise TypeError("Argument must be a list of addresses.")

        # Check if each element in the list of addresses is of type str.
        if not all([isinstance(address, str) for address in address_list]):
            raise TypeError(
                "All addresses in the list must be of string format")

        # Check if list has at least 4 elements:
        if len(address_list) < 4:
            raise ValueError("List must contain at least four addresses")

        # getting formatted list of address
        formatted_address_list = self._format_address_list(address_list)

        # requesting coordinates of each address
        coordinates_list = asyncio.run(
            self._request_coordinates(formatted_address_list))

        # bundling together coordinates and orginal addresses
        coords_and_addrs_list = self._bundle_coords_and_addrs(
            address_list, coordinates_list)

        # separate starting and final address from intermediate addresses
        departure_address, arrival_address, delivery_addresses = self._separate_addresses(
            coords_and_addrs_list)

        # request optmized route
        optimized_route_response = asyncio.run(self._request_route(
            departure_address, delivery_addresses, arrival_address))

        # extract ordered list of addresses for optimal route from json response
        optimized_route_list = self._extract_optimized_route(
            optimized_route_response, delivery_addresses)

        return optimized_route_list

    def _separate_addresses(self, coords_and_addrs_list):
        """
        Internal function to separate starting and final addresses from intermediate addresses.

        Args:
            coords_and_addrs_list (list): list of coordinates and addresses

        Returns:
            dict: departure address dict
            dict: arrival address dict
            list of dict: intermediate delivery addresses
        """
        departure_address = coords_and_addrs_list.pop(0)

        arrival_address = coords_and_addrs_list.pop(-1)

        return departure_address, arrival_address, coords_and_addrs_list

    def _extract_optimized_route(self, response_str, delivery_addresses):
        """
        Internal function to extract the ordered optimal route.

        Args:
            response_str (str): json string that was returned from the routing API.
            delivery_addresses (list of dict): list of dicts containing all intermediate destinations

        Returns:
            list: optimized (ordered) list of delivery destinations.
        """

        # convert json string to dictionary
        response_dict = json.loads(response_str)

        # check if response has any error
        if response_dict["code"] > 0:
            raise Exception(response_dict["error"])

        # initialize list to be returned
        optimized_route = []

        # iterating over each step of the route
        for step in response_dict["routes"][0]["steps"]:
            if step["type"] == "job":
                for i, address in enumerate(delivery_addresses):
                    if i == step["job"]:
                        optimized_route.append(address["address"])

        return optimized_route

    async def _request_route(self, departure_address, delivery_addresses, arrival_address):
        """
        Internal function that send a post request to the routing API and receives back the optimized route.

        Args:
            departure_address (dict): dict containing lat (float), lng (float)      and address (str) of the departure address
            delivery_addresses (list of dict): list of dicts the addresses to       be optimized (same structure as departure and arrival dicts).
            arrival_address (dict): dict containing lat (float), lng (float)        and address (str) of the arrival address.

        Returns:
            json string: json response from post request containing optimal route.
        """

        POST_URL = 'http://solver.vroom-project.org'

        optimized_addresses = {}

        # building the structure for the POST request
        # OBS: lat and lng must be reversed inside the 'start', 'end' and 'jobs'
        # lists. Correct request order: ['lng', 'lat']
        request_structure_dict = {
            'vehicles': [
                {
                    'id': 0,
                    'start': [
                        departure_address['lng'],
                        departure_address['lat']
                    ],
                    'end': [
                        arrival_address['lng'],
                        arrival_address['lat']
                    ]
                }
            ],
            'jobs': [],
            'options': {
                'g': True
            }
        }

        # iterate over delivery addresses to add them to the 'jobs' list
        for i, address in enumerate(delivery_addresses):
            request_structure_dict['jobs'].append({
                'id': i,
                'location': [
                    address['lng'],
                    address['lat']
                ]
            })

        # Sending post request
        request = await httpx.post(POST_URL, json=request_structure_dict)

        return request.text

    def _bundle_coords_and_addrs(self, address_list, coordinates_list):
        """
        Internal function that bundles together a list of address and it's coordinates.

        Args:
            address_list (list of str): list of addresses
            coordinates_list (list of tuples of floats): list of tuples of          coordinates

        Returns:
            list of dicts: list composed of dicts of coordinates and address.
        """
        coords_and_addrs_list = []

        for i in range(len(address_list)):
            aux_dict = {}
            aux_dict['lat'] = coordinates_list[i][0]
            aux_dict['lng'] = coordinates_list[i][1]
            aux_dict['address'] = address_list[i]

            coords_and_addrs_list.append(aux_dict)

        return coords_and_addrs_list

    async def _request_coordinates(self, formatted_address_list):
        """
        Internal function that receives a list of formatted addresses and requests it's coordinates.

        Args:
            formatted_address_list (list of str): List of formatted addresses       to be used to get coordinates of the addresses.

        Returns:
            list of tuples of floats: A list containing all coordinates
        """
        coordinates_list = []

        for address in formatted_address_list:

            # Format full url for request
            url = "http://www.mapquestapi.com/geocoding/v1/address?key={}&location={}".format(
                self.map_quest_api_key, address)

            # send get request for coordinates
            request = await httpx.get(url)

            # extract lat and lng from json response
            rjson = request.json()
            try:
                lat = rjson['results'][0]['locations'][0]['latLng']['lat']
                lng = rjson['results'][0]['locations'][0]['latLng']['lng']
            except IndexError:
                raise SystemExit("Unable to fetch coordinates for address {}".format(
                    rjson['results'][0]['providedLocation']['location'].replace("+", " ")))

            # append to list of coordinates
            coordinates_list.append((float(lat), float(lng),))

        return coordinates_list

    def _format_address_list(self, address_list):
        """
        Internal function that replaces spaces with plus sign to be used in the url string.

        Args:
            address_list (list of str): the unformatted list of addresses inputted by the user.

        Returns:
            list of str: Formatted list of addresses.
        """

        return [address.replace(" ", "+") for address in address_list]
