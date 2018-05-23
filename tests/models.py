def lhc_model_2017(jmad):
    modeldef = jmad.model_packs['jmad-modelpack-lhc'].branches['master'].models['LHC 2017']
    return jmad.create_model(modeldef)