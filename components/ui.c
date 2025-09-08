#include "ui.h"
#include "lvgl.h"

void ui_init() {
    lv_init();  // Inicializa LVGL

    // Aquí deberías inicializar el controlador de pantalla y táctil
    // usando esp_lcd_ili9341 y esp_lcd_touch_xpt2046

    // Ejemplo: crear una etiqueta en pantalla
    lv_obj_t *label = lv_label_create(lv_scr_act());
    lv_label_set_text(label, "¡Hola, Antonio!");
    lv_obj_align(label, LV_ALIGN_CENTER, 0, 0);
}