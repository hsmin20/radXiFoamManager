import os
import sys
from shutil import copytree
import subprocess
from datetime import datetime
import getpass
from PyQt5.QtWidgets import QApplication, QMainWindow, QDesktopWidget, QFileDialog, QVBoxLayout, \
    QWidget, QPushButton, QGridLayout, QLabel, QLineEdit, QGroupBox, QTextEdit, QRadioButton, QHBoxLayout, QCheckBox


class RadXiFoamManager:
    BLOCK_MESH_FILE = "blockMeshDict"
    FIELD_DICT_FILE = "setFieldsDict"
    COMBUSTION_PROPERTIES_FILE = "combustionProperties"
    CONTROL_DICT_FILE = "controlDict"

    BLOCK_MESH_FILE_TEMP = "blockMeshDict_Template"
    FIELD_DICT_FILE_TEMP = "setFieldsDict_Template"
    COMBUSTION_PROPERTIES_FILE_TEMP = "combustionProperties_Template"
    CONTROL_DICT_FILE_TEMP = "controlDict_Template"

    def __init__(self, wd, wh, wt, tt, h2_volFrac, h2o_volFrac, probeLocations, email):
        self.wallDistance = float(wd)
        self.wallHeight = float(wh)
        self.wallThickness = float(wt)
        self.tentThickness = float(tt)
        self.H2VolumeFraction = float(h2_volFrac)
        self.H2OVolumeFraction = float(h2o_volFrac)
        self.probeLocations = probeLocations
        self.email = email

    def replaceBlockMeshDictFile(self, content):
        # START_X = 1
        # END_X = 28
        IGNITION_X = 6.1

        strBox1 = "//Box 1, Point 0, 1, 2, 3, 4, 5, 6, 7\n"
        strBox1 += "\t(1\t0\t" + str(self.wallHeight) + ")\n"
        strBox1 += "\t(" + str(IGNITION_X) + "\t0\t" + str(self.wallHeight) + ")\n"
        strBox1 += "\t(" + str(IGNITION_X) + "\t5\t" + str(self.wallHeight) + ")\n"
        strBox1 += "\t(1\t5\t" + str(self.wallHeight) + ")\n"
        strBox1 += "\t(1\t0\t11)\n"
        strBox1 += "\t(" + str(IGNITION_X) + "\t0\t11)\n"
        strBox1 += "\t(" + str(IGNITION_X) + "\t5\t11)\n"
        strBox1 += "\t(1\t5\t11)\n"

        strBox2 = "\n\t//Box 2 Point 8, 9, 10, 11\n"
        strBox2 += "\t(1\t0\t0)\n"
        strBox2 += "\t(" + str(IGNITION_X) + "\t0\t0)\n"
        strBox2 += "\t(" + str(IGNITION_X) + "\t5\t0)\n"
        strBox2 += "\t(1\t5\t0)\n"

        strBox3 = "\n\t//Box 3 Point 12, 13, 14, 15\n"
        strBox3 += "\t(" + str(IGNITION_X + self.wallDistance) + "\t0\t" + str(self.wallHeight) + ")\n"
        strBox3 += "\t(" + str(IGNITION_X + self.wallDistance) + "\t5\t" + str(self.wallHeight) + ")\n"
        strBox3 += "\t(" + str(IGNITION_X + self.wallDistance) + "\t0\t11)\n"
        strBox3 += "\t(" + str(IGNITION_X + self.wallDistance) + "\t5\t11)\n"

        # strBox4 = "\n\t//Box 4\n"

        strBox5 = "\n\t//Box 5 Point 16, 17, 18, 19, 20, 21, 22, 23\n"
        strBox5 += "\t(" + str(IGNITION_X + self.wallDistance + self.wallThickness) + "\t0\t" + str(self.wallHeight) + ")\n"
        strBox5 += "\t(28\t0\t" + str(self.wallHeight) + ")\n"
        strBox5 += "\t(28\t5\t" + str(self.wallHeight) + ")\n"
        strBox5 += "\t(" + str(IGNITION_X + self.wallDistance + self.wallThickness) + "\t5\t" + str(self.wallHeight) + ")\n"
        strBox5 += "\t(" + str(IGNITION_X + self.wallDistance + self.wallThickness) + "\t0\t11)\n"
        strBox5 += "\t(28\t0\t11)\n"
        strBox5 += "\t(28\t5\t11)\n"
        strBox5 += "\t(" + str(IGNITION_X + self.wallDistance + self.wallThickness) + "\t5\t11)\n"

        strBox6 = "\n\t//Box 6 Point 24, 25\n"
        strBox6 += "\t(" + str(IGNITION_X + self.wallDistance) + "\t0\t0)\n"
        strBox6 += "\t(" + str(IGNITION_X + self.wallDistance) + "\t5\t0)\n"

        strBox7 = "\n\t//Box 7 Point 26, 27, 28, 29\n"
        strBox7 += "\t(" + str(IGNITION_X + self.wallDistance + self.wallThickness) + "\t0\t0)\n"
        strBox7 += "\t(28\t0\t0)\n"
        strBox7 += "\t(28\t5\t0)\n"
        strBox7 += "\t(" + str(IGNITION_X + self.wallDistance + self.wallThickness) + "\t5\t0)\n"

        content = content.replace('BOX_1', strBox1)
        content = content.replace('BOX_2', strBox2)
        content = content.replace('BOX_3', strBox3)
        content = content.replace('BOX_5', strBox5)
        content = content.replace('BOX_6', strBox6)
        content = content.replace('BOX_7', strBox7)

        return content

    def calculateMassFraction(self, H2_vf, H2O_vf):
        O2_vf = (1 - (H2_vf + H2O_vf)) * 0.21
        N2_vf = (1 - (H2_vf + H2O_vf)) * 0.79

        mm = [2, 32, 28, 18]

        vf = [H2_vf, O2_vf, N2_vf, H2O_vf]

        mf = []
        mTot = 0

        for i in range(4):
            mTot = mTot + (mm[i] * vf[i])

        for i in range(4):
            mf.append((mm[i] * vf[i]) / mTot)

        H2_ratio = mf[0] / mf[1]
        H2_eq_ratio = H2_ratio / 0.125  # 0.125 = stoichiometry H2/O2 mass ratio
        H2_alpha = 2.18 - (0.8 * (H2_eq_ratio - 1))
        H2_beta = -0.16 + 0.22 * (H2_eq_ratio - 1)

        # H2 mass fraction, H2O mass fraction, N2 mass fraction, equivalence ratio, H2 alpha, H2 beta
        return mf[0], mf[3], mf[2], H2_eq_ratio, H2_alpha, H2_beta

    def makeProbeLocations(self):
        pl = self.probeLocations
        pl = pl.replace("),", ")\n")
        pl = pl.replace(",", " ")
        return pl

    def replaceAndWriteFiles(self, template_dir, dest_path):
        blockMeshDictFile = template_dir + self.BLOCK_MESH_FILE_TEMP
        f = open(blockMeshDictFile, "r")
        content = f.read()
        f.close()

        content = self.replaceBlockMeshDictFile(content)

        # create blockMeshDict file
        fullname = dest_path + r"/system/" + self.BLOCK_MESH_FILE
        f = open(fullname, "w")
        f.write(content)
        f.close()

        h2_m_fraction, h2o_m_fraction, n2_m_fraction, eq_ratio, alpha, beta = self.calculateMassFraction(
            self.H2VolumeFraction, self.H2OVolumeFraction)

        setFieldsDictFile = template_dir + self.FIELD_DICT_FILE_TEMP
        f = open(setFieldsDictFile, "r")
        content = f.read()
        f.close()

        content = content.replace('VOL_SCALAR_FIELD_VALUE_FT', str(h2_m_fraction))
        content = content.replace('VOL_SCALAR_FIELD_VALUE_N2', str(n2_m_fraction))
        content = content.replace('VOL_SCALAR_FIELD_VALUE_H2O', str(h2o_m_fraction))

        fullname = dest_path + r"/system/" + self.FIELD_DICT_FILE
        f = open(fullname, "w")
        f.write(content)
        f.close()

        combustionPropertiesFile = template_dir + self.COMBUSTION_PROPERTIES_FILE_TEMP
        f = open(combustionPropertiesFile, "r")
        content = f.read()
        f.close()

        content = content.replace('EQUIVALENCE_RATIO', str(eq_ratio))
        content = content.replace('H2_ALPHA', str(alpha))
        content = content.replace('H2_BETA', str(beta))

        fullname = dest_path + r"/constant/" + self.COMBUSTION_PROPERTIES_FILE
        f = open(fullname, "w")
        f.write(content)
        f.close()

        controlDictFile = template_dir + self.CONTROL_DICT_FILE_TEMP
        f = open(controlDictFile, "r")
        content = f.read()
        f.close()

        probeLocations = self.makeProbeLocations()
        content = content.replace('PROBE_LOCATIONS', probeLocations)

        fullname = dest_path + r"/system/" + self.CONTROL_DICT_FILE
        f = open(fullname, "w")
        f.write(content)
        f.close()


class RadXiFoamWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.initUI()

    def showTempDirDialog(self):
        folder_dialog = QFileDialog(self)
        folder_dialog.setWindowTitle('Select Template Folder')
        folder_dialog.setFileMode(QFileDialog.Directory)
        folder_dialog.setOption(QFileDialog.ShowDirsOnly, True)
        folder_dialog.setOption(QFileDialog.DontUseNativeDialog, True)
        folder_dialog.setOption(QFileDialog.ReadOnly, False)
        # folder_dialog.setOption(QFileDialog.AcceptMode, QFileDialog.AcceptOpen)

        if folder_dialog.exec_() == QFileDialog.Accepted:
            selected_folders = folder_dialog.selectedFiles()
            self.editTempDir.setText(selected_folders[0])

    def showSrcDirDialog(self):
        folder_dialog = QFileDialog(self)
        folder_dialog.setWindowTitle('Select Source Folder')
        folder_dialog.setFileMode(QFileDialog.Directory)
        folder_dialog.setOption(QFileDialog.ShowDirsOnly, True)
        folder_dialog.setOption(QFileDialog.DontUseNativeDialog, True)
        folder_dialog.setOption(QFileDialog.ReadOnly, False)
        # folder_dialog.setOption(QFileDialog.AcceptMode, QFileDialog.AcceptOpen)

        if folder_dialog.exec_() == QFileDialog.Accepted:
            selected_folders = folder_dialog.selectedFiles()
            self.editSrcDir.setText(selected_folders[0])

    def showDstDirDialog(self):
        folder_dialog = QFileDialog(self)
        folder_dialog.setWindowTitle('Select Destination Folder')
        folder_dialog.setFileMode(QFileDialog.Directory)
        folder_dialog.setOption(QFileDialog.ShowDirsOnly, True)
        folder_dialog.setOption(QFileDialog.DontUseNativeDialog, True)
        folder_dialog.setOption(QFileDialog.ReadOnly, False)
        # folder_dialog.setOption(QFileDialog.AcceptMode, QFileDialog.AcceptOpen)

        if folder_dialog.exec_() == QFileDialog.Accepted:
            selected_folders = folder_dialog.selectedFiles()
            self.editDstDir.setText(selected_folders[0])

    def initTemplateOption(self):
        groupbox = QGroupBox('Folders')

        tempDirLabel = QLabel('Template directory')
        self.editTempDir = QLineEdit(r"/home/dahan/OpenFOAM/tutorial/SRI_radXiFoamTemplate/")
        self.editTempDir.setFixedWidth(600)
        openTempDirBtn = QPushButton('...')
        openTempDirBtn.clicked.connect(self.showTempDirDialog)

        srcDirLabel = QLabel('Source directory')
        self.editSrcDir = QLineEdit(r"/home/dahan/OpenFOAM/tutorial/SRI_radXiFoamTemplate/Source")
        self.editSrcDir.setFixedWidth(600)
        openSrcDirBtn = QPushButton('...')
        openSrcDirBtn.clicked.connect(self.showSrcDirDialog)

        dstDirLabel = QLabel('Destination directory')
        self.editDstDir = QLineEdit(r"/home/dahan/OpenFOAM/tutorial/")
        self.editDstDir.setFixedWidth(600)
        openDstDirBtn = QPushButton('...')
        openDstDirBtn.clicked.connect(self.showDstDirDialog)

        layout = QGridLayout()
        layout.addWidget(tempDirLabel, 0, 0)
        layout.addWidget(self.editTempDir, 0, 1)
        layout.addWidget(openTempDirBtn, 0, 2)
        layout.addWidget(srcDirLabel, 1, 0)
        layout.addWidget(self.editSrcDir, 1, 1)
        layout.addWidget(openSrcDirBtn, 1, 2)
        layout.addWidget(dstDirLabel, 2, 0)
        layout.addWidget(self.editDstDir, 2, 1)
        layout.addWidget(openDstDirBtn, 2, 2)
        groupbox.setLayout(layout)

        return groupbox

    def initCFDOption(self):
        groupbox = QGroupBox('CFD parameters')

        label2 = QLabel('Barrier Wall Position and Dimension')
        labelWD = QLabel('Wall Distance(m)')
        self.editWD = QLineEdit('5.1')
        labelWH = QLabel('Wall Height(m)')
        self.editWH = QLineEdit('2.0')
        labelWT = QLabel('Wall Thickness(m)')
        self.editWT = QLineEdit('0.1')

        label3 = QLabel('Tent Dimension')
        labelTT = QLabel('Tent Thickness(m)')
        self.editTT = QLineEdit('2.2')

        label4 = QLabel('H2 and H2O Volume Fraction')
        labelH2VF = QLabel('H2 Volume Fraction')
        self.editH2VF = QLineEdit('0.2')
        labelH2OVF = QLabel('H2O Volume Fraction')
        self.editH2OVF = QLineEdit('0.2')

        label5 = QLabel('Probe Locations')
        labelProbe = QLabel('(x,y,z) format locations')
        self.editProbes = QLineEdit('(1,0,0),(2,0,0),(5,0,0),(6,0,0),(7,0,0)')
        self.editProbes.setFixedWidth(600)

        label6 = QLabel('Requester Information')
        labelEmail = QLabel('Email (used for calculation folder name)')
        self.editEmail = QLineEdit('abc@def.co.kr')

        layout = QGridLayout()
        layout.addWidget(label2, 0, 0)
        layout.addWidget(labelWD, 1, 0)
        layout.addWidget(self.editWD, 1, 1)
        layout.addWidget(labelWH, 1, 2)
        layout.addWidget(self.editWH, 1, 3)
        layout.addWidget(labelWT, 1, 4)
        layout.addWidget(self.editWT, 1, 5)
        layout.addWidget(label3, 2, 0)
        layout.addWidget(labelTT, 3, 0)
        layout.addWidget(self.editTT, 3, 1)
        layout.addWidget(label4, 4, 0)
        layout.addWidget(labelH2VF, 5, 0)
        layout.addWidget(self.editH2VF, 5, 1)
        layout.addWidget(labelH2OVF, 5, 2)
        layout.addWidget(self.editH2OVF, 5, 3)
        layout.addWidget(label5, 6, 0)
        layout.addWidget(labelProbe, 7, 0)
        layout.addWidget(self.editProbes, 7, 1, 1, 6)
        layout.addWidget(label6, 8, 0)
        layout.addWidget(labelEmail, 9, 0)
        layout.addWidget(self.editEmail, 9, 1, 1, 2)
        groupbox.setLayout(layout)

        return groupbox

    def initCommandOption(self):
        groupbox = QGroupBox('Command && Logs')

        requestBtn = QPushButton('Start CFD Calculation')
        requestBtn.clicked.connect(self.startCFDCalculation)
        self.radioSingle = QRadioButton('Single-Core', self)
        self.radioSingle.setChecked(True)
        self.radioMulti = QRadioButton(self)
        self.radioMulti.setText('Multi-Core (16)')
        self.cbOnline = QCheckBox('Online Enabled (for report)', self)
        self.cbOnline.setChecked(True)

        self.messageTE = QTextEdit(self, readOnly=True)

        layout = QGridLayout()
        layout.addWidget(self.messageTE, 0, 0, 1, 3)
        layout.addWidget(requestBtn, 1, 0)
        layout.addWidget(self.radioSingle, 1, 1)
        layout.addWidget(self.radioMulti, 1, 2)
        layout.addWidget(self.cbOnline, 1, 3)
        groupbox.setLayout(layout)

        return groupbox

    def initUI(self):
        self.setWindowTitle('RadXiFoam V2.0 GUI Application')

        layout = QVBoxLayout()
        layout.addWidget(self.initTemplateOption())
        layout.addWidget(self.initCFDOption())
        layout.addWidget(self.initCommandOption())

        self.statusBar().showMessage('Welcome to RadXiFoam GUI')
        self.central_widget = QWidget()  # define central widget
        self.setCentralWidget(self.central_widget)  # set QMainWindow.centralWidget

        self.centralWidget().setLayout(layout)

        self.resize(400, 800)
        self.center()
        self.show()

    def center(self):
        qr = self.frameGeometry()
        cp = QDesktopWidget().availableGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())

    def copyReportHtml(self, dest_dir, sWallDistance, sWallHeight, sWallThickness, sTentThickness, sH2Fraction,
                       sH2OFraction, sensorPositions):

        reportTemplateFile = './kaeri_CFD_result_TEMPLATE_offline.html'
        if self.cbOnline.isChecked():
            reportTemplateFile = './kaeri_CFD_result_TEMPLATE_online.html'
        f = open(reportTemplateFile, "r")
        content = f.read()
        f.close()

        content = content.replace('WALL_DISTANCE', sWallDistance)
        content = content.replace('WALL_HEIGHT', sWallHeight)
        content = content.replace('WALL_THICKNESS', sWallThickness)
        content = content.replace('TENT_WIDTH', sTentThickness)
        content = content.replace('H2_VOLFRAC', sH2Fraction)
        content = content.replace('H2O_VOLFRAC', sH2OFraction)
        content = content.replace('SENSOR_POSITIONS', sensorPositions)
        content = content.replace('EMAIL_ADDR', getpass.getuser())

        date = datetime.now()
        datestr = date.strftime("%Y-%m-%d %H:%S")
        content = content.replace('DATE_NOW', datestr)

        sWallDistance10x = str(float(sWallDistance) * 10)
        sWallHeight10x = str(float(sWallHeight) * 10)
        sWallThickness10x = str(float(sWallThickness) * 10)
        sTentThickness10x = str(float(sTentThickness) * 10)

        content = content.replace('WALL_10X_DISTANCE', sWallDistance10x)
        content = content.replace('WALL_10X_HEIGHT', sWallHeight10x)
        content = content.replace('WALL_10X_THICKNESS', sWallThickness10x)
        content = content.replace('TENT_10X_WIDTH', sTentThickness10x)

        sensorPos2 = "".join(sensorPositions.split()) #remove whitespaces
        sensorPos2 = sensorPos2.replace("(", "")
        sensorPos2 = sensorPos2.replace(")", "")
        sensorList = sensorPos2.split(',')
        sensorSize = int(len(sensorList) / 3)

        columnString = '<th scope="cols"></th>'
        for i in range(sensorSize):
            newColumn = '<th scope="cols">P' + str(i) + '</th>'
            columnString = columnString + '\n' + newColumn

        rowString = ''
        for i in range(sensorSize):
            newRow = '<td><input type="checkbox" value=' + str(i) + 'id="check' + str(i) + '" name="check' + str(i) + '" /></td>'
            rowString = rowString + '\n' + newRow

        content = content.replace('TABLE_COLUMN', columnString)
        content = content.replace('TABLE_ROW', rowString)


        fullname = dest_dir + r"/kaeri_CFD_result.html"
        f = open(fullname, "w")
        f.write(content)
        f.close()

    def startCFDCalculation(self):
        self.messageTE.setText('')
        self.messageTE.append('radXiFoamManager calculation starts....')

        template_dir = self.editTempDir.text()
        self.messageTE.append('template folder = ' + template_dir)

        email = self.editEmail.text()
        curtime = datetime.now().strftime('%Y%m%d%H%M%S')
        srcDir = self.editSrcDir.text()
        dstDir = self.editDstDir.text()
        destination_dir = dstDir + email + "_" + curtime
        self.messageTE.append('destination folder = ' + destination_dir)

        try:
            copytree(srcDir, destination_dir)
            self.messageTE.append('all sources are copied to destination.')

            os.system("chmod 775 -R " + destination_dir)
            self.messageTE.append('Folder permissions are changed')

            sWallDistance = self.editWD.text()
            sWallHeight = self.editWH.text()
            sWallThickness = self.editWT.text()
            sTentThickness = self.editTT.text()
            sH2Fraction = self.editH2VF.text()
            sH2OFraction = self.editH2OVF.text()
            probeLocations = self.editProbes.text()

            wallDistance = float(sWallDistance)
            wallHeight = float(sWallHeight)
            wallThickness = float(sWallThickness)
            tentThickness = float(sTentThickness)
            H2Fraction = float(sH2Fraction)
            H2OFraction = float(sH2OFraction)

            radXi = RadXiFoamManager(wallDistance, wallHeight, wallThickness, tentThickness, H2Fraction, H2OFraction,
                                     probeLocations, email)

            radXi.replaceAndWriteFiles(template_dir, destination_dir)

            self.messageTE.append('Mesh file and other properties files are written and copied.')

            self.copyReportHtml(destination_dir, sWallDistance, sWallHeight, sWallThickness, sTentThickness,
                                sH2Fraction, sH2OFraction, probeLocations)

            self.messageTE.append('Report file is written and copied.')

            os.chdir(destination_dir)

            runscript = destination_dir + r"/runScript.sh"
            if self.radioMulti.isChecked():
                runscript = destination_dir + r"/runScript_multi.sh"
            self.messageTE.append('running script : ' + runscript)

            cp = subprocess.Popen(runscript, cwd=destination_dir)
            self.messageTE.append('Script returned ' + str(cp))

            self.messageTE.append('Calculation started. Wait for it to be finished')
        except FileNotFoundError as err:
            self.messageTE.append(err.args[0])

if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = RadXiFoamWindow()
    sys.exit(app.exec_())
