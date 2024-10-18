from bitstring import BitArray
from typing import List
from PIL import Image
import numpy as np
import numpy.typing as npt
import os

class StematographyTools:
    @staticmethod
    def convert_string_to_binary(text: str, bits_per_char: int = 8) -> str:
        try:
            binary_text = BitArray(bytes=text.encode('ascii')).bin
            return binary_text
        except UnicodeEncodeError:
            raise Exception(f"The ordinal code for {text} is not in the range 128. Please enter text that only contains 8-bit ascii.")
        
    @staticmethod
    def convert_binary_to_string(binary_text: str, bits_per_char: int = 8) -> str:
        try:
            if len(binary_text) % bits_per_char != 0:
                raise ValueError("The binary text length is not a multiple of the bits per character.")

            byte_chunks = [binary_text[i:i + bits_per_char] for i in range(0, len(binary_text), bits_per_char)]
            ascii_text = ''.join([chr(int(byte, 2)) for byte in byte_chunks])

            return ascii_text
        except ValueError as e:
            raise Exception(f"Error converting binary to string: {e}")

    @staticmethod
    def convert_binary_to_8bit_int(binary_value: str) -> int:
        return int(binary_value, 2)

    @staticmethod
    def convert_8bit_int_to_binary(val: int) -> str:
        if 0 <= val <= 255:
            return format(val, '08b')
        else:
            raise Exception(f"{val} cannot be represented by 8 bits")

    @staticmethod
    def convert_image_to_binary_array(file_path: str) -> npt.NDArray[np.str_]:
        try:
            image = Image.open(file_path).convert('RGBA') 
            rgba_array = np.array(image)

            binary_rgba_array = np.vectorize(StematographyTools.convert_8bit_int_to_binary)(rgba_array)

            return binary_rgba_array
        except FileNotFoundError:
            raise Exception(f"{file_path} was not found, check if the path is correct.")

    @staticmethod
    def encode_LSB(pixel: List[str], char_binary: str) -> List[str]:
        for i in range(min(len(pixel), len(char_binary))):
            pixel[i] = pixel[i][:-1] + char_binary[i]
        return pixel
    
    @staticmethod
    def decode_LSB(pixel: List[str]) -> str:
        binary_segment = ""
        for p in pixel:
            binary_segment += p[-1] 
        return binary_segment


    @staticmethod
    def encrypt_binary_into_image(binary_text: str, image_binary_array: npt.NDArray[np.str_]) -> npt.NDArray[np.str_]:
        text_index = 0
        total_bits = len(binary_text)
        for i in range(image_binary_array.shape[1]):  # w
            for j in range(image_binary_array.shape[0]):  # h
                if text_index + 3 <= total_bits:
                    pixel = image_binary_array[j, i]
                    bits_to_embed = binary_text[text_index:text_index + 3]
                    modified_pixel = StematographyTools.encode_LSB(pixel.tolist(), bits_to_embed)
                    image_binary_array[j, i] = np.array(modified_pixel)  
                    text_index += 3
                else:
                    break
            if text_index >= total_bits:
                break

        return image_binary_array

    @staticmethod
    def create_new_image(image_binary_array: npt.NDArray[np.str_], path: str) -> None:
        int_rgba_array = np.vectorize(StematographyTools.convert_binary_to_8bit_int)(image_binary_array).astype(np.uint8)
        reconstructed_image = Image.fromarray(int_rgba_array, 'RGBA')

        reconstructed_image.save(path)
        print(f"Image saved to {path}")

    @staticmethod
    def encrypt(text: str, image_path: str) -> None:
        if (len(text) * (8 / 3) < os.stat(image_path).st_size):
            binary_text = StematographyTools.convert_string_to_binary(text)
            binary_image_array = StematographyTools.convert_image_to_binary_array(image_path)
            binary_image_array = StematographyTools.encrypt_binary_into_image(binary_text, binary_image_array)

            split_path = os.path.splitext(image_path)
            file_name = split_path[0]
            
            print(binary_text)
            StematographyTools.create_new_image(binary_image_array, f"{file_name}_encoded.png")
        else:
            raise OverflowError("Text is too large for image!")
        
    @staticmethod
    def decrypt(image_path: str, text_length: int) -> str:
        binary_text = ""
        total_bits = text_length * 8 
        bits_extracted = 0

        image_binary_array = StematographyTools.convert_image_to_binary_array(image_path)
        for i in range(image_binary_array.shape[1]):  # w
            for j in range(image_binary_array.shape[0]):  # h
                if bits_extracted + 3 <= total_bits:
                    pixel = image_binary_array[j, i]
                    binary_segment = StematographyTools.decode_LSB(pixel)
                    binary_text += binary_segment
                    bits_extracted += 3
                else:
                    break
            if bits_extracted >= total_bits:
                break
        
        print(binary_text[:total_bits])
        return StematographyTools.convert_binary_to_string(binary_text[:total_bits])  # Limit to exact bit length


StematographyTools.encrypt(text="password", image_path="tree.jpg")
print(StematographyTools.decrypt(image_path="tree_encoded.png", text_length=8))

