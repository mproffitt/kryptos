from itertools import combinations

alphabet = [
    'A', 'B', 'C', 'D', 'E', 'F', 'G',
    'H', 'I', 'J', 'K', 'L', 'M', 'N',
    'O', 'P', 'Q', 'R', 'S', 'T', 'U',
    'V', 'W', 'X', 'Y', 'Z'
]

rulesengine = None

cache = {
    'calculator': None
}
cache_locked = False

def a2i(ch):
    return alphabet.index(ch.upper()) + 1

def i2a(i):
    return alphabet[(i-1)]

def distanceto(x, y):
    """
    Addition vector moving through Z

    :param x The starting character
    :param y The character to calculate the distance to

    :return char
    """
    a = a2i(x)
    b = a2i(y)
    c = (26 - a) + b
    return i2a(c % 26)

def distancefrom(x, y):
    """
    Subtraction vector moving through Z

    :param x The starting character
    :param y The character to calculate the distance to

    :return char
    """
    a = a2i(x)
    b = a2i(y)

    c = ((26 - a) - b)
    return i2a(c % 26)

def polarity(string):
    """
    Returns O if all characters in string are odd, E if all are even or M if there is a mix
    """
    return (
        'E' if all(j % 2 == 0 for j in [a2i(t) for t in string])
        else 'O' if all(not (j % 2 == 0) for j in [a2i(t) for t in string])
        else 'M'
    )

def distance_calculator(start, end):
    """
    Calculates a table of distances between the start and end positions

    This will return a 97x26 grid of all possible positions.
    Because it takes so long to build, the result of this is
    stored in memory for re-use throughout the cipher.
    """
    global cache_locked, cache
    while cache_locked:
        sleep(0.1)

    if not cache['calculator']:
        cache_locked = True
        distances = [
            (start, polarity(start)),
            (end, polarity(end)),
        ]
        completed = []
        for pos in range(26):
            for item in combinations([d[0] for d in distances], 2):
                if item in completed:
                    continue
                c = item[0]
                s = item[1]
                for i in range(6):
                    z = ''
                    for j in range(len(c)):
                        z += distanceto(c[j], s[j])

                    e = polarity(z)
                    if (z, e) not in distances:
                        distances.append((z, e))
                        p = ' '.join([str(a2i(t)).zfill(2) for t in z])
                    c = s
                    s = z

                completed.append(item)
            pos += 1

        cache['calculator'] = distances
        cache_locked = False
    return cache['calculator']
