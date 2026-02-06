#include <Arduino.h>
#include <Adafruit_NeoPixel.h>

#define LED_BRIGHTNESS 40

Adafruit_NeoPixel *strip = new Adafruit_NeoPixel(700, 6, NEO_GRB + NEO_KHZ800);

void setup()
{
  Serial.begin(115200);
  while (!Serial)
    ;
  strip->begin();
  strip->setBrightness(LED_BRIGHTNESS);
  strip->clear();
  strip->show();
}

bool power_on = false;

uint16_t op_buffer;
bool read_op = false;

int color_size = 0;

uint32_t palette[127];

bool await_bytes(int amnt)
{
  __ULong start = millis();
  while (Serial.available() < amnt)
  {
    __ULong now = millis();
    if (now - start > 1000L)
      return false;
  }
  return true;
}

void handle_toggle_power()
{
  strip->clear();
  power_on = (op_buffer & 0b00100000) >> 5;
  strip->show();
}

void handle_load_palette()
{
  int palette_size = *((char *)&op_buffer + 1);
  for (int i = 0; i < palette_size; i++)
  {
    if (!await_bytes(4))
      return;
    Serial.readBytes((char *)&palette[i], 4);
  }
  color_size = (op_buffer & 0b00111000) >> 3;
}

void handle_show_colors()
{
  int horizontal = (op_buffer & 0b00100000) >> 5;
  uint16_t starting_point = (op_buffer & 0xFF % 4) * 256 + (op_buffer >> 8 & 0xFF);

  int start_x = starting_point / 35;
  bool up_column = start_x % 2 == 1;
  int lights_from_edge = starting_point - 35 * start_x;
  int pixel_idx = starting_point;

  char current_byte = 0;
  if (!await_bytes(1))
    return;
  Serial.readBytes(&current_byte, 1);
  int latest_color_id = 0;
  int bit_idx = 0;
  while (true)
  {
    latest_color_id = ((current_byte >> max(8 - bit_idx - color_size, 0)) &
                       (int)pow(2, min(8 - bit_idx, color_size)) - 1);
    if (8 - bit_idx < color_size)
    {
      if (!await_bytes(1))
        break;
      Serial.readBytes(&current_byte, 1);
      int remaining_size = color_size + bit_idx - 8;
      latest_color_id <<= remaining_size;
      latest_color_id |= ((current_byte >> (8 - remaining_size)) &
                          (int)pow(2, remaining_size) - 1);
      bit_idx -= 8;
    }
    bit_idx += color_size;
    if (latest_color_id == pow(2, color_size) - 1)
      break;
    if (power_on)
    {
      pixel_idx %= 700;
      strip->setPixelColor(pixel_idx, palette[latest_color_id]);
      if (horizontal)
      {
        pixel_idx += up_column ? 2 * lights_from_edge + 1 : 69 - 2 * lights_from_edge;
        up_column ^= 0x1;
      }
      else
        pixel_idx += pow(-1, up_column);
    }
  }
}

int FPS = 60;
__ULong FRAME_SIZE = 1000 / FPS;

void loop()
{
  __ULong frame_start = millis();
  if (await_bytes(2))
  {
    read_op = true;
    int bytesRead = Serial.readBytes((char *)&op_buffer, 2);
    if (op_buffer == 0xFF00)
    {
      __ULong end_of_frame = millis();
      __ULong remaining_frame_time = FRAME_SIZE + frame_start - end_of_frame;
      if (remaining_frame_time > 0)
        delay(remaining_frame_time);
      strip->show();
    }
    else
    {
      char op = (op_buffer & 0b11000000) >> 6;
      switch (op)
      {
      case 0:
        handle_toggle_power();
        break;
      case 1:
        handle_load_palette();
        break;
      case 2:
        handle_show_colors();
        break;
      }
    }
  }
  Serial.write(0xFF);
}

// OPs:
// [0] Toggle Power
//   - Bit [2] is on or off

// [1] Send color pallete
//   - Bits [2-4] is exponent for resolution of pallete
//   - Bits [8-15] is size of pallete

// [2] Send colors indexes to pixels from start point
//   - Bit [2] is horizontal or vertical scan
//   - Bits [6-15] is start point

// [3] Wipe pixels from start point
//   - Bit [2] is horizontal or vertical scan
//   - Bits [6-15] is start point