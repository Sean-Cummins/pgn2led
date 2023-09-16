import sys
import io
import argparse
from PIL import Image

PNG_HEADER = b'\x89\x50\x4e\x47\x0d\x0a\x1a\x0a'

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('input', nargs='*', default = sys.stdin, 
        help='files to read, if empty, stdin is used')
    args = parser.parse_args()

    try:
        while True:
            if args.input[0] == '-':

                header = sys.stdin.buffer.read(8)

                if header == PNG_HEADER:

                    png = io.BytesIO()

                    png.write(header)

                    for chunk in ['IDHR', 'IDAT', 'IEND']:

                        chunk_bytes = io.BytesIO()

                        length = sys.stdin.buffer.read(4)
                        name = sys.stdin.buffer.read(4)
                        data = sys.stdin.buffer.read(int(length.hex(), 16))
                        crc = sys.stdin.buffer.read(4)

                        chunk_bytes.write(length)
                        chunk_bytes.write(name)
                        chunk_bytes.write(data)
                        chunk_bytes.write(crc)

                        png.write(chunk_bytes.getvalue())

                    png.seek(0)

                    img = Image.open(png)
                    img.save('out2.png', 'PNG')

            else:
                print('Do Files')
                break
        
    except KeyboardInterrupt:
        sys.stdout.flush()
        pass
