'''Test Case 1
Only two objects in the scene, on big object on the ground, and one small object on top of the big object
'''

import pybullet as p
import os
from Config.constants import WORKSPACE_LIMITS, colors_lower, colors_upper, TARGET_LOWER, TARGET_UPPER, COLOR_SPACE
import numpy as np

class TestCase1:
    def __init__(self, env):
        self.env = env
        self.bottom_obj_size_ranges = {
            'length': [0.89, 0.9], # [0.35, 0.37], # [0.349, 0.500], # [0.2, 0.21], # # length is along x-axis when orientation yaw = 0
            'width': [0.89, 0.9], # [0.35, 0.37], # [0.250, 0.500],
            'height': [0.08, 0.1]
        }
        self.top_obj_size_ranges = {
            'length': [0.08, 0.1],
            'width': [0.08, 0.1],
            'height': [0.01, 0.04]
        }
        self.workspace_center = [(WORKSPACE_LIMITS[0][0] + WORKSPACE_LIMITS[0][1])/2, (WORKSPACE_LIMITS[1][0] + WORKSPACE_LIMITS[1][1])/2, 0] # (x, y, z) - workspace center
        self.bottom_pos_range = [
            [self.workspace_center[0]-0.001, self.workspace_center[1]-0.001, self.workspace_center[2] + self.bottom_obj_size_ranges['height'][1]/2 + 0.01], 
            [self.workspace_center[0]+0.001, self.workspace_center[1]+0.001, self.workspace_center[2] + self.bottom_obj_size_ranges['height'][1]/2 + 0.005]
        ]  # Constant for now (x1, y1, z1) -> (x2, y2, z2)
        self.obj_colors =  {
            'bottom_obj': np.hstack([COLOR_SPACE[3, :], np.array([1.0])]),
            'target_obj': np.hstack([COLOR_SPACE[0, :], np.array([1.0])]), # np.hstack([(TARGET_LOWER.astype(float)+TARGET_UPPER.astype(float))/(255.0*2), np.array([1.0])]),
            'marker': np.hstack([COLOR_SPACE[9, :], np.array([1.0])])
        }
        self.current_bottom_obj_height = 0
        self.current_bottom_size = np.zeros(shape=(3, ))
        self.current_target_size = np.zeros(shape=(3, ))
        self.current_bottom_6d_pose = np.zeros(shape=(6, ))
        # self.current_bottom_orn = np.zeros(shape=(3, ))

    def create_obj(self, obj_pos, obj_orientation, half_extents=np.array([0.08, 0.08, 0.02]) , obj_type='bottom_obj'):
        '''Create the object with desired properties and return the object id
        '''
        body_id_target = None
        if obj_type=='marker':
            vuid = self.env.client_id.createVisualShape(p.GEOM_BOX, halfExtents=half_extents, rgbaColor=self.obj_colors[obj_type])# np.hstack([(TARGET_LOWER.astype(float)+TARGET_UPPER.astype(float))/(255.0*2), np.array([1.0])]))
            body_id_target = self.env.client_id.createMultiBody(baseVisualShapeIndex=vuid, basePosition=obj_pos, baseOrientation=obj_orientation)
        else:
            cuid = self.env.client_id.createCollisionShape(p.GEOM_BOX, halfExtents = half_extents)
            vuid = self.env.client_id.createVisualShape(p.GEOM_BOX, halfExtents=half_extents, rgbaColor=self.obj_colors[obj_type])# np.hstack([(TARGET_LOWER.astype(float)+TARGET_UPPER.astype(float))/(255.0*2), np.array([1.0])]))
            body_id_target = self.env.client_id.createMultiBody(baseMass=0.1, baseCollisionShapeIndex=cuid, baseVisualShapeIndex=vuid, basePosition=obj_pos, baseOrientation=obj_orientation)
        # p.changeVisualShape(body_id_target, rgbaColor=self.obj_colors[obj_type])
        return body_id_target

    def add_marker_obj(self, obj_pos, obj_orientation, half_extents=np.array([0.08, 0.08, 0.02]) , obj_type='marker'):
        if self.check_target_within_bottom_bounds(obj_pos) == False:
            print("Failed!!!!!!!!!!!!!")
            return 0, False
        # marker_obj_id = self.create_obj(obj_pos, obj_orientation, half_extents=half_extents, obj_type=obj_type)
        # marker_obj_id = self.env.client_id.loadURDF("/home/susiejojo/Mid-Level-Planner/Assets/custom/multi_colored.urdf", obj_pos, obj_orientation)
        vuid = self.env.client_id.createVisualShape(p.GEOM_MESH, fileName='/home/susiejojo/Mid-Level-Planner/Assets/custom/multi_colored.obj')
        marker_obj_id = self.env.client_id.createMultiBody(baseVisualShapeIndex=vuid, basePosition=obj_pos, baseOrientation=obj_orientation)
        p.changeVisualShape(marker_obj_id,-1,rgbaColor=[1,1,1,0.5])

        self.env.add_object_id(marker_obj_id)
        success = True
        success &= self.env.wait_static()
        for _ in range(5):
            self.env.client_id.stepSimulation()
        return marker_obj_id, success

    def create_specific_test_case(self, bottom_obj='default', target_obj='test', targetPos=[0, 0]):
        '''Samples a randomly generated test case with the required properties
        1. One object on the top
        2. One object at the bottom


        cubeStartOrientation = p.getQuaternionFromEuler([0, 0, 0])
        '''
        body_ids = []
        success = True
        obj_file = os.path.join("Assets", "blocks", 'rect.urdf') #'rect.urdf')

        # Define bottom object properties
        bottom_obj_size = np.random.uniform(
            low=[self.bottom_obj_size_ranges['length'][0], self.bottom_obj_size_ranges['width'][0], self.bottom_obj_size_ranges['height'][0]],
            high=[self.bottom_obj_size_ranges['length'][1], self.bottom_obj_size_ranges['width'][1], self.bottom_obj_size_ranges['height'][1]],
            size=(3, )
        )
        self.current_bottom_obj_height = bottom_obj_size[2]
        self.current_bottom_size = bottom_obj_size
        bottom_obj_pos = np.random.uniform(
            low=self.bottom_pos_range[0], 
            high=self.bottom_pos_range[1], 
            size=(3, ))

        bottom_obj_orientation = None

        euler_vals = None
        if bottom_obj=='default':
            euler_vals = [0, 0, 0]
            bottom_obj_orientation = p.getQuaternionFromEuler(euler_vals)
        elif bottom_obj=='random':
            euler_vals = [0, 0, np.random.uniform(low=0, high=2*np.pi)]
            bottom_obj_orientation = p.getQuaternionFromEuler(euler_vals)

        self.current_bottom_6d_pose[0:3] = bottom_obj_pos
        self.current_bottom_6d_pose[3:6] = euler_vals
        # Define target object properties

        target_obj_size = np.random.uniform(
            low=[self.top_obj_size_ranges['length'][0], self.top_obj_size_ranges['width'][0], self.top_obj_size_ranges['height'][0]],
            high=[self.top_obj_size_ranges['length'][1], self.top_obj_size_ranges['width'][1], self.top_obj_size_ranges['height'][1]],
            size=(3, )
        )
        if target_obj=='train':
            self.current_target_size = target_obj_size
        elif target_obj=='test':
            self.current_target_size = np.array([0.09, 0.12, 0.03])

        is_valid_pos = False
        target_obj_pos = None
        while not is_valid_pos:
            # print("Yo")
            target_obj_pos = np.random.uniform(
                low=[bottom_obj_pos[0] - bottom_obj_size[0]/2, bottom_obj_pos[1] - bottom_obj_size[1]/2, bottom_obj_pos[2] + bottom_obj_size[2]/2 + target_obj_size[2]/2 + 0.03], # bottom_obj_pos[0] + bottom_obj_size[0]//2 - 0.001],
                high=[bottom_obj_pos[0] + bottom_obj_size[0]/2, bottom_obj_pos[1] + bottom_obj_size[1]/2, bottom_obj_pos[2] + bottom_obj_size[2]/2 + target_obj_size[2]/2 + 0.04],
                size=(3, )
            )
            is_valid_pos = self.check_target_within_bottom_bounds(target_obj_pos)

        target_obj_pos[0] = targetPos[0]
        target_obj_pos[1] = targetPos[1]

        target_obj_orientation = p.getQuaternionFromEuler([0, 0, np.random.uniform(low=0, high=2*np.pi)])

        # Create bottom object
        bottom_obj_id = self.create_obj(bottom_obj_pos, bottom_obj_orientation, half_extents=np.array(bottom_obj_size)/2, obj_type='bottom_obj')
        body_ids.append(bottom_obj_id)
        self.env.add_object_id(bottom_obj_id)

        # Create target object
        target_obj_id = None
        if target_obj=='train':
            target_obj_id = self.create_obj(target_obj_pos, target_obj_orientation, half_extents=np.array(target_obj_size)/2, obj_type='target_obj')
        elif target_obj=='test':
            target_obj_id = self.env.client_id.loadURDF("/home/susiejojo/Mid-Level-Planner/Assets/custom/multi_colored.urdf",target_obj_pos, target_obj_orientation)
            p.changeVisualShape(target_obj_id,-1,rgbaColor=[1,1,1,1])
        body_ids.append(target_obj_id)
        self.env.add_object_id(target_obj_id)

        # No collision objects
        success &= self.env.wait_static()
        success &= self.env.wait_static()

        # print("Loading a new scene! ---------------------------------------- : {}".format(success))
        # give time to stop
        for _ in range(5):
            self.env.client_id.stepSimulation()
            # p.stepSimulation(self.env.client_id)

        return body_ids, success


    def sample_test_case(self, bottom_obj='default', target_obj='train'):
        '''Samples a randomly generated test case with the required properties
        1. One object on the top
        2. One object at the bottom


        cubeStartOrientation = p.getQuaternionFromEuler([0, 0, 0])
        '''
        body_ids = []
        success = True
        obj_file = os.path.join("Assets", "blocks", 'rect.urdf') #'rect.urdf')

        # Define bottom object properties
        bottom_obj_size = np.random.uniform(
            low=[self.bottom_obj_size_ranges['length'][0], self.bottom_obj_size_ranges['width'][0], self.bottom_obj_size_ranges['height'][0]],
            high=[self.bottom_obj_size_ranges['length'][1], self.bottom_obj_size_ranges['width'][1], self.bottom_obj_size_ranges['height'][1]],
            size=(3, )
        )
        self.current_bottom_obj_height = bottom_obj_size[2]
        self.current_bottom_size = bottom_obj_size
        bottom_obj_pos = np.random.uniform(
            low=self.bottom_pos_range[0], 
            high=self.bottom_pos_range[1], 
            size=(3, ))

        bottom_obj_orientation = None

        euler_vals = None
        if bottom_obj=='default':
            euler_vals = [0, 0, 0]
            bottom_obj_orientation = p.getQuaternionFromEuler(euler_vals)
        elif bottom_obj=='random':
            euler_vals = [0, 0, np.random.uniform(low=0, high=2*np.pi)]
            bottom_obj_orientation = p.getQuaternionFromEuler(euler_vals)

        self.current_bottom_6d_pose[0:3] = bottom_obj_pos
        self.current_bottom_6d_pose[3:6] = euler_vals
        # Define target object properties

        target_obj_size = np.random.uniform(
            low=[self.top_obj_size_ranges['length'][0], self.top_obj_size_ranges['width'][0], self.top_obj_size_ranges['height'][0]],
            high=[self.top_obj_size_ranges['length'][1], self.top_obj_size_ranges['width'][1], self.top_obj_size_ranges['height'][1]],
            size=(3, )
        )
        if target_obj=='train':
            self.current_target_size = target_obj_size
        elif target_obj=='test':
            self.current_target_size = np.array([0.09, 0.12, 0.03])

        is_valid_pos = False
        target_obj_pos = None
        while not is_valid_pos:
            # print("Yo")
            target_obj_pos = np.random.uniform(
                low=[bottom_obj_pos[0] - bottom_obj_size[0]/2, bottom_obj_pos[1] - bottom_obj_size[1]/2, bottom_obj_pos[2] + bottom_obj_size[2]/2 + target_obj_size[2]/2 + 0.03], # bottom_obj_pos[0] + bottom_obj_size[0]//2 - 0.001],
                high=[bottom_obj_pos[0] + bottom_obj_size[0]/2, bottom_obj_pos[1] + bottom_obj_size[1]/2, bottom_obj_pos[2] + bottom_obj_size[2]/2 + target_obj_size[2]/2 + 0.04],
                size=(3, )
            )
            is_valid_pos = self.check_target_within_bottom_bounds(target_obj_pos)

        target_obj_orientation = p.getQuaternionFromEuler([0, 0, np.random.uniform(low=0, high=2*np.pi)])

        # Create bottom object
        bottom_obj_id = self.create_obj(bottom_obj_pos, bottom_obj_orientation, half_extents=np.array(bottom_obj_size)/2, obj_type='bottom_obj')
        body_ids.append(bottom_obj_id)
        self.env.add_object_id(bottom_obj_id)

        # Create target object
        target_obj_id = None
        if target_obj=='train':
            target_obj_id = self.create_obj(target_obj_pos, target_obj_orientation, half_extents=np.array(target_obj_size)/2, obj_type='target_obj')
        elif target_obj=='test':
            target_obj_id = self.env.client_id.loadURDF("/home/susiejojo/Mid-Level-Planner/Assets/custom/multi_colored.urdf",target_obj_pos, target_obj_orientation)
            p.changeVisualShape(target_obj_id,-1,rgbaColor=[1,1,1,1])
        body_ids.append(target_obj_id)
        self.env.add_object_id(target_obj_id)

        # No collision objects
        success &= self.env.wait_static()
        success &= self.env.wait_static()

        # print("Loading a new scene! ---------------------------------------- : {}".format(success))
        # give time to stop
        for _ in range(5):
            self.env.client_id.stepSimulation()
            # p.stepSimulation(self.env.client_id)

        return body_ids, success

    def check_target_within_bottom_bounds(self, target_obj_pos):
        '''Checks if the target object is within the bottom object bounds
        '''
        yaw = self.current_bottom_6d_pose[5]
        target_cartesian_pos = target_obj_pos[0:2]
        bottom_com = self.current_bottom_6d_pose[0:2]
        target_wrt_bottom_com = target_cartesian_pos - bottom_com
        orn_vec = np.array([np.cos(yaw), np.sin(yaw)])
        orn_perpendicular = np.array([-np.sin(yaw), np.cos(yaw)])

        ext1 = abs(np.dot(orn_vec, target_wrt_bottom_com)) - self.current_bottom_size[0]/2 # length component
        ext2 = abs(np.dot(orn_perpendicular, target_wrt_bottom_com)) - self.current_bottom_size[1]/2 # breadth/width component

        if ext1 < 0 and ext2 < 0:
            return True
        else:
            return False

    def create_standard(self):
        '''Standard test case - both the objects at the center of the workspace
        '''
        body_ids = []
        success = True

        obj_file = os.path.join("Assets", "blocks", 'rect.urdf') #'rect.urdf')
        obj_positions = {
            'bottom_obj': [(WORKSPACE_LIMITS[0][0] + WORKSPACE_LIMITS[0][1])/2, (WORKSPACE_LIMITS[1][0] + WORKSPACE_LIMITS[1][1])/2, 2.349930442869663239e-02*10],
            'target_obj': [(WORKSPACE_LIMITS[0][0] + WORKSPACE_LIMITS[0][1])/2, (WORKSPACE_LIMITS[1][0] + WORKSPACE_LIMITS[1][1])/2, 2.349930442869663239e-02*25 ]
        }
        scales = {
            'bottom_obj': 3,
            'normal_obj': 1
        }

        # obj_colors =  {
        #     'bottom_obj': [list(colors_lower[2].astype(float)/255.0).append(1)]
        # }

        # print("COLORS ----------------") 
        # print(list(np.hstack([colors_lower[4].astype(float)/255.0, np.array([1.0])])))
        # print(np.hstack([(colors_upper[4]+colors_lower[4]).astype(float)/(2*255.0), np.array([1.0])]))

        body_id_bottom = self.env.client_id.loadURDF(
                obj_file, obj_positions['bottom_obj'], globalScaling=scales['bottom_obj']
            )
        self.env.client_id.changeVisualShape(body_id_bottom, -1, rgbaColor=np.hstack([COLOR_SPACE[3, :], np.array([1.0])]))# np.hstack([(colors_upper[4]+colors_lower[4]).astype(float)/(2*255.0), np.array([1.0])]))
        body_ids.append(body_id_bottom)

        # body_id_target = p.loadURDF(
        #         obj_file, obj_positions['target_obj'], globalScaling=scales['normal_obj']
        #     )
        # p.changeVisualShape(body_id_target, -1, rgbaColor=np.hstack([(TARGET_LOWER.astype(float)+TARGET_UPPER.astype(float))/(255.0*2), np.array([1.0])]))
        # body_ids.append(body_id_target)

        cuid = self.env.client_id.createCollisionShape(p.GEOM_BOX, halfExtents = [0.05, 0.05, 0.01])
        vuid = self.env.client_id.createVisualShape(p.GEOM_BOX, halfExtents=[0.05, 0.05, 0.01], rgbaColor=np.hstack([(TARGET_LOWER.astype(float)+TARGET_UPPER.astype(float))/(255.0*2), np.array([1.0])]))
        obj_id = self.env.client_id.createMultiBody(baseMass=0.1, baseCollisionShapeIndex=cuid, baseVisualShapeIndex=vuid, basePosition=obj_positions['target_obj'])
        #p.changeVisualShape(cuid, -1, rgbaColor=np.hstack([(TARGET_LOWER.astype(float)+TARGET_UPPER.astype(float))/(255.0*2), np.array([1.0])]))
        body_ids.append(obj_id)

        success &= self.env.wait_static()
        success &= self.env.wait_static()

        print("Success ---------------------------------------- : {}".format(success))
        print(body_ids)
        # give time to stop
        for _ in range(5):
            self.env.client_id.stepSimulation(self.env.client_id)

        return body_ids, success
