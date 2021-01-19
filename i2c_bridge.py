import flower


class I2CBridge():
    map = {
        'I2C_WRITE_REG' : 0x7C,
        'I2C_READ_REG'  : 0x7B,
        'I2C_DATA_REG'  : 0x22
        }

    def __init__(self):
        self.dev = flower.Flower()

    def read(self, reg):
        #data to send
        spi_data = [self.map['I2C_WRITE_REG'], 1, reg & 0xFF, 0]
        #write address to i2c bridge
        self.dev.write(self.dev.DEV_FLOWER, spi_data)
        #print self.dev.readRegister(self.dev.DEV_FLOWER, self.map['I2C_WRITE_REG'])
        #toggle an i2c read (address pulsed)
        self.dev.write(self.dev.DEV_FLOWER, [self.map['I2C_READ_REG'], 0, 0, 0])
        #i2c data should show up in the i2c_data_reg
        i2c_read_data = self.dev.readRegister(self.dev.DEV_FLOWER, self.map['I2C_DATA_REG'])
        return i2c_read_data
    
    def write(self, reg, cmd):
        #data to send
        spi_data = [self.map['I2C_WRITE_REG'], 0, reg & 0xFF, cmd & 0xFF]
        #write to i2c bridge
        self.dev.write(self.dev.DEV_FLOWER, spi_data)


    def test(self):
        None


if __name__=='__main__':

    d = I2CBridge()

    for i in range(0, 30, 1):
        print d.read(i)
