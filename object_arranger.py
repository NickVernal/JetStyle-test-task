import time
import math
import json
import os
import argparse

from PIL import Image, ImageDraw


class HomeObject:
    """
    Size constants for home object.
    """
    WIDTH = 350
    EDGE = 196
    HEIGHT = int((EDGE ** 2 - (WIDTH / 2) ** 2) ** 0.5) * 2
    HALF_WIDTH = int(WIDTH / 2)
    HALF_HEIGHT = int(HEIGHT / 2)


class BlockObject:
    """
    Size constants for block object.
    Block contains 12 (or less) home objects.
    """
    WIDTH = HomeObject.WIDTH * 4
    HEIGHT = HomeObject.HEIGHT * 4
    DY = HEIGHT + HomeObject.HALF_HEIGHT
    DX = WIDTH + HomeObject.HALF_WIDTH
    HALF_DX = int(DX / 2)
    HALF_DY = int(DY / 2)
    HOME_AMT = 12


class Map:
    def __init__(self, object_amount):
        self.__argument_check(object_amount)
        self._object_amount = object_amount
        self._block_amount = math.ceil(object_amount / BlockObject.HOME_AMT)
        self._blocks = self._arrange_blocks()
        self._size = self._get_size()
        self._coordinates = self._get_coordinates()

    def draw(self, file_name: str, path: str):
        """
        Creates an image and fills it with all home objects.
        Then saves it to a file.
        """
        transparent = (255, 255, 255, 0)
        half_transparent = (255, 0, 0, 127)

        size = self._size
        img = Image.new('RGBA', size, transparent)
        drw = ImageDraw.Draw(img)

        for pos in self._coordinates:
            drw.polygon(self._get_home_full_coord(pos), fill=half_transparent, outline=transparent)

        img.save(os.path.join(path, file_name + '.png'), 'PNG')

    def save_to_json(self, file_name, path):
        """
        Saves required data to a file in json format.
        """
        width, height = self._size
        result = {
            'width': width,
            'height': height,
            'coordinates': self._coordinates
        }
        with open(os.path.join(path, file_name + '.json'), 'w') as f:
            json.dump(result, f)

    def _arrange_blocks(self):
        """
        This method arranges blocks by rows and columns.
        The purpose is to get appropriate ratio.
        """

        # needs to improve row-column ratio
        ratio_coefficient = 1 if self._block_amount < 2 else 4 / 3

        rows = int(math.ceil(self._block_amount ** 0.5 * ratio_coefficient))
        columns = int(self._block_amount / rows)
        remainder = self._block_amount % rows

        result = [columns for _ in range(rows)]

        """
        We fill rows with the same amount of blocks. Then we need to distribute
        leftover blocks between the rows.
        Odd rows are shifted to the left relative to even rows, that's why
        we add leftover blocks to odd rows at first and then to even rows.  
        """
        complemented = [x for x in range(1, rows, 2)] + [x for x in range(0, rows, 2)]

        index = 0
        while remainder > 0:
            result[complemented[index]] += 1
            index += 1
            remainder -= 1

        return result

    def _get_inner_coordinates(self, x_start: int, y_start: int, to_build: int, even: bool):
        """
        Returns coordinates of all home objects in specific block.
        :param x_start: x coordinate of block
        :param y_start: y coordinate of block
        :param to_build: amount of home objects in block
        :param even: Block direction (even/odd)
        :return: list of coordinates
        """
        def get_homes_coordinates(index, _sign, amount):
            x = int(x_start + HomeObject.WIDTH * coefficient[0][index])
            y = int(y_start + HomeObject.HEIGHT * coefficient[1][index])

            return [(x + _sign * i * HomeObject.HALF_WIDTH, y + i * HomeObject.HALF_HEIGHT)
                    for i in range(amount)]

        coefficient = [[[1.5, 2.25, 3], [-1.5, -0.75, 0]],
                       [[1.5, 0.75, 0], [-1.5, -0.75, 0]]][int(even)]

        result = []
        sign = 1 if even else -1

        for j in range(int(to_build / 4)):
            result += get_homes_coordinates(j, sign, 4)
        if to_build < BlockObject.HOME_AMT:
            result += get_homes_coordinates(int(to_build / 4), sign, to_build % 4)

        return result

    def _get_certain_block_pos(self, row: int, col: int):
        """
        Returns coordinates of block which is located in certain column and row
        """
        x = 0
        y = BlockObject.HEIGHT / 2

        if not row % 2 and len(self._blocks) > 1:
            x += BlockObject.DX / 2

        x += BlockObject.DX * col
        y += BlockObject.HALF_DY * row

        return int(x), int(y)

    def _get_coordinates(self):
        """
        Returns coordinates of all home objects.
        """
        result = []
        amount = self._object_amount
        for i in range(len(self._blocks)):
            for j in range(self._blocks[i]):
                to_build = BlockObject.HOME_AMT if amount > BlockObject.HOME_AMT else amount
                amount -= BlockObject.HOME_AMT
                x, y = self._get_certain_block_pos(i, j)
                result += self._get_inner_coordinates(x, y, to_build, not i % 2)

        return result

    def _get_size(self):
        """
        Returns the size of required picture
        """
        height = BlockObject.HEIGHT + (len(self._blocks) - 1) * BlockObject.HALF_DY

        blocks_in_line = max(self._blocks)

        width = BlockObject.WIDTH + (blocks_in_line - 1) * BlockObject.DX

        if self._blocks[0] == blocks_in_line and len(self._blocks) > 1:
            width += BlockObject.HALF_DX

        return math.ceil(width), math.ceil(height)

    def _get_home_full_coord(self, start: tuple):
        """
        Returns all four coordinates of current home object
        :param start: coordinate of current home object
        :return: list of coordinates
        """
        return [start,
                (start[0] + HomeObject.HALF_WIDTH, start[1] - HomeObject.HALF_HEIGHT),
                (start[0] + HomeObject.WIDTH, start[1]),
                (start[0] + HomeObject.HALF_WIDTH, start[1] + HomeObject.HALF_HEIGHT)]

    def __argument_check(self, amount):
        if type(amount) is not int or amount < 1:
            raise ValueError('Natural number was expected.')

if __name__ == '__main__':
    parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)

    parser.add_argument('amount', type=int, help='object amount')
    parser.add_argument('-d', '--dir', type=str, help='output directory', default='out')
    parser.add_argument('-i', '--img', type=str, help='output image name', default='image')
    parser.add_argument('-j', '--json', type=str, help='output json name', default='json_data')

    args = parser.parse_args()

    dir_exists = os.path.isdir(args.dir)
    if not dir_exists:
        print('there is no such directory. Create? (Y/N)')
        while True:
            answer = input()
            if answer.lower() in ['y', 'yes']:
                os.makedirs(args.dir)
                dir_exists = True
                break
            elif answer.lower() in ['n', 'now']:
                print('This program cannot be executed.')
                break

    if dir_exists:
        start_time = time.time()
        m = Map(args.amount)
        m.save_to_json(args.json, args.dir)
        print("Execution time (JSON) = %s seconds" % (time.time() - start_time))
        start_time = time.time()
        m.draw(args.img, args.dir)
        print("Execution time (Image) = %s seconds" % (time.time() - start_time))
