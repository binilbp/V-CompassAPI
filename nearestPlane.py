def find_nearest_plane(planes, target_lat, target_lon, target_alt=0):
    nearest_plane = None
    min_distance = float("inf")

    for plane in planes:
        dist = distance_3d(
            target_lat,
            target_lon,
            target_alt,
            plane["lat"],
            plane["lon"],
            plane["altitude_m"],
        )

        if dist < min_distance:
            min_distance = dist
            nearest_plane = plane

    return nearest_plane, min_distance


def distance_3d(lat1, lon1, alt1, lat2, lon2, alt2):
    ground_distance = haversine_distance(lat1, lon1, lat2, lon2)
    altitude_diff = abs((alt2 or 0) - (alt1 or 0))
    return sqrt(ground_distance**2 + altitude_diff**2)


from math import radians, sin, cos, sqrt, atan2


def haversine_distance(lat1, lon1, lat2, lon2):
    R = 6371000  # Earth radius in meters

    # convert degrees to radians
    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])

    dlat = lat2 - lat1
    dlon = lon2 - lon1

    a = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))

    return R * c  # distance in meters
