# laad straling van elk weermodel, de locatie_IDs als grid nummers x en y

m = Sequential()

m.add(k.input(shape=(1, weermodel_n, x, y)))
m.add(k.Conv3D())
m.add(BatchNormalization())
