#include "../param/param_obot_g474.h"
#include "../st_device.h"
#include "../../motorlib/peripheral/stm32g4/spi_dma.h"
#include "../../motorlib/qep_encoder.h"
#include "../../motorlib/ads1235.h"
#include "../../motorlib/gpio.h"

using TorqueSensor = ADS1235;
using MotorEncoder = QEPEncoder;
using OutputEncoder = EncoderBase;

extern "C" void SystemClock_Config();
void pin_config_obot_g474_motor_r0();

struct InitCode {
    InitCode() {
      SystemClock_Config();
      pin_config_obot_g474_motor_r0();        
        //SPI3 ADS1235
        DMAMUX1_Channel0->CCR =  DMA_REQUEST_SPI3_TX;
        DMAMUX1_Channel1->CCR =  DMA_REQUEST_SPI3_RX;
        SPI3->CR1 = SPI_CR1_CPHA | SPI_CR1_MSTR | (4 << SPI_CR1_BR_Pos) | SPI_CR1_SSI | SPI_CR1_SSM | SPI_CR1_SPE;    // baud = clock/32
        SPI3->CR2 = (7 << SPI_CR2_DS_Pos) | SPI_CR2_FRXTH;    // 8 bit   
    }
};

namespace config {
    const uint32_t main_loop_frequency = 10000;    
    const uint32_t pwm_frequency = 50000;
    InitCode init_code;

    GPIO torque_sensor_cs(*GPIOD, 2, GPIO::OUTPUT);
    QEPEncoder motor_encoder(*TIM2);
    SPIDMA spi_dma(*SPI3, torque_sensor_cs, *DMA1_Channel1, *DMA1_Channel2, 1000, 1000);
    ADS1235 torque_sensor(spi_dma, ADS1235::GAIN_1, ADS1235::SPS_1200);
    OutputEncoder output_encoder;
};

#include "../../motorlib/boards/config_obot_g474_motor.cpp"

void config_init() {
    System::log("torque_sensor_init: " + std::to_string(config::torque_sensor.init()));

    System::api.add_api_variable("torque", new const APIFloat(&config::torque_sensor.torque_));
    //System::api.add_api_variable("decimation", new APIUint16(&config::torque_sensor.decimation_));
}

void config_maintenance() {}