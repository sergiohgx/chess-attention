import json

from config import TRAIN_FOLDER, ROOT_DIR
from evaluator import Evaluator
from models import AttentionEncoderDecoderModel
import zipfile
import os
from predictor import Predictor
from trainer import TrainerController

'''
  model = ModelController();
  model.load()

  // para test
  model.initTrainSession()
  model.train( 'dataset-x')
  model.save()

  // se tiver começado, continua onde parou, caso contrario inicia e salva
  model.trainOrContinueForCurriculum( 'curriculum-1', 200, 0.1, [ 'level1', 'level2', 'level3'])

    // salva nivel corrente em 'current-level.txt'
    // salva log de acuracia e loss para cada step, com informacoes de data,hora,level,epoch
    // cria checkpoint manager e salva 


  model.restoreFromCurriculum( 'curriculum-1')
  model.predict()
'''


class ModelPredictController:

    def __init__(self,
                 ):
        self.model = None

    def load(self):
        self.model = AttentionEncoderDecoderModel().build()

    def useModel(self, model):
        self.model = model
        return self

    def restoreFromBestCheckpoint(self):
        bestCheckpointPath = ROOT_DIR + '/train-folder/checkpoints/train_comparativo_20211106_handwritten_teacher_10k_'
        self.model.steps.restoreFromLatestCheckpoint(bestCheckpointPath)

    def restoreFromCheckpointName(self, trainName):
        checkPointPath = TRAIN_FOLDER + '/checkpoints/' + trainName
        self.model.steps.restoreFromLatestCheckpoint(checkPointPath)

    def restoreFromCheckpointRelativePath(self, relativePath):
        self.model.steps.restoreFromLatestCheckpoint(relativePath)

    def predictOneImage(self, imagePath, _len=16):
        result = self.model.steps.evaluate(imagePath, _length=_len)
        return result

    def evaluateForTest(self, dataset='test', plot_attention=False, _len=4):
        evaluator = Evaluator(self.model, _len)
        return evaluator.evaluate_test_data(dataset, plot_attention)

    def predictZip(self):
        pass

    def train(self):
        pass

    def save(self):
        pass

    def trainWith(self, level):
        pass

    def resetMetrics(self):
        pass

    def getConfig(self):
        pass

    def getMetrics(self):
        pass


def uncompressToFolder(zipFile, uncompressFolder):
    if os.path.isdir(uncompressFolder):
        print(uncompressFolder, ' already exists. Skip uncompress..')
        return

    print('unzipping ', zipFile, ' to ', uncompressFolder)
    with zipfile.ZipFile(zipFile, 'r') as zip_ref:
        zip_ref.extractall(uncompressFolder)
    print('unzipping ', zipFile, ' to ', uncompressFolder, ' done!')


def save_train_log(trainName, logs):
    logFile = TRAIN_FOLDER + '/log/' + trainName + ".txt"
    with open(logFile, 'w') as file:
        for log in logs:
            file.write(json.dumps(log) + '\n')
    print('arquivo de log gerado em ', logFile)


class Saver:
    def __init__(self, trainName, model):
        self.trainName = trainName
        self.model = model

    def __call__(self, tag=None):
        name = self.trainName + '_latest' if tag is None else self.trainName + '_' + tag
        checkPointPath = TRAIN_FOLDER + '/checkpoints/' + name
        self.model.steps.saveCheckpointTo(checkPointPath)
        print('checkpoint saved to ' + checkPointPath)


class ModelTrainController:
    def __init__(self,
                 ):
        self.bestCheckpointPath = 'C:/mestrado/repos-github/chess-attention/trained--for-evaluation/notebooks' \
                                  '/best_checkpoint/1006/checkpoints/train '
        self.model = None
        self.trainer = None

    def load(self):
        self.model = AttentionEncoderDecoderModel().build()

    def useModel(self, model):
        self.model = model

    def initTrainSession(self, BATCH_SIZE=32):
        self.trainer = TrainerController(self.model, BATCH_SIZE=BATCH_SIZE)

    def restoreFromBestCheckpoint(self):
        bestCheckpointPath = ROOT_DIR + '/train-folder/checkpoints/train_comparativo_20211106_handwritten_teacher_10k_'
        self.model.steps.restoreFromLatestCheckpoint(bestCheckpointPath)

    def restoreFromCheckpointName(self, trainName):
        checkPointPath = TRAIN_FOLDER + '/checkpoints/' + trainName
        self.model.steps.restoreFromLatestCheckpoint(checkPointPath)

    def restoreFromCheckpointRelativePath(self, relativePath):
        self.model.steps.restoreFromLatestCheckpoint(relativePath)

    def evaluateForTest(self, dataset='test', _len=4):
        evaluator = Evaluator(self.model, _len)
        return evaluator.evaluate_test_data(dataset)

    def prepareDatasetForTrain(self, datasetZipFileOrFolder, sampled=False, use_sample=(0.1, 0.1)):
        # uncompress for train

        if datasetZipFileOrFolder.endswith('.zip'):
            print('preparing dataset from zip file ', datasetZipFileOrFolder)
            uncompressFolder = TRAIN_FOLDER + '/tmp/' + os.path.basename(datasetZipFileOrFolder).replace('.zip', '')
            uncompressToFolder(datasetZipFileOrFolder, uncompressFolder)
        else:
            uncompressFolder = datasetZipFileOrFolder

        # prepare dataset
        self.trainer.prepareFilesForTrain(uncompressFolder, sampled, use_sample)
        print('Dataset from zip file ', datasetZipFileOrFolder, ' ready for training')

    def trainUntil(self, target_loss, target_acc, min_max_epoch, lens=[4], train_name='none', test_set=None):
        saver = Saver(trainName=train_name, model=self.model)
        print('starting trainUntil loss={} or acc={} epoch={}-{}'.format( target_loss, target_acc, min_max_epoch, train_name))
        self.trainer.trainUntil(target_loss, target_acc, min_max_epoch, lens, train_name, test_set=test_set,
                                saver=saver)

        print('starting trainUntil ', target_loss, min_max_epoch, train_name, ' DONE!')

    def save(self, trainName):
        checkPointPath = TRAIN_FOLDER + '/checkpoints/' + trainName
        self.model.steps.saveCheckpointTo(checkPointPath)
        print('model saved to ' + checkPointPath)

    def levelCheckpointExists(self, trainName):
        checkPointPath = TRAIN_FOLDER + '/checkpoints/' + trainName
        return self.model.steps.checkpointExists(checkPointPath)

    def trainOrContinueForCurriculum(self,
                                     curriculumName,
                                     levelsDatasetZipFiles,
                                     target_loss,
                                     target_acc,
                                     min_max_epoch,
                                     sampled=False,
                                     use_sample=(0.1, 0.1), lens=[4], test_set=None):

        if self.levelCheckpointExists(curriculumName):
            print('treino já finalizado. Checkpoint em ', self.levelCheckpointExists(curriculumName));
            return

        skip = True
        for levelZipFile in levelsDatasetZipFiles:
            checkpointName = "{}--{}".format(curriculumName, os.path.basename(levelZipFile).replace('.zip', ''))

            if skip and self.levelCheckpointExists(checkpointName):
                # se treino ja foi finalizado, somente recupera..
                print('treino para ', checkpointName, ' ja realizado. Recupera checkpoint')
                ModelPredictController().useModel(self.model).restoreFromCheckpointName(checkpointName)
            else:
                # caso contrario, faz o treinamento
                print('treino para ', checkpointName, ' NAO realizado. Realiza treinamento.')
                self.prepareDatasetForTrain(levelZipFile, sampled, use_sample)
                self.trainUntil(target_loss, target_acc, min_max_epoch, lens, checkpointName, test_set)
                self.save(checkpointName)
                skip = False

                # valida no testset, até o tamanho maximo infoamdo
                # evaluator = Evaluator(self.model, target_len=lens[-1])
                # test_acc = evaluator.evaluate_test_data('teste' if self.NUM_LINHAS == 2 else 'test-8lines')

                # salva em aquivo
                save_train_log(checkpointName, self.trainer.logs)

        self.save(curriculumName)
        print('treinamento de curriculo finalizado com sucesso!')
