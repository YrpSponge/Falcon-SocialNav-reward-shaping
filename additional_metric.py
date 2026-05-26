#!/usr/bin/env python3

# This source code is licensed under the MIT license found in the
# LICENSE file in the root directory of this source tree.


# from typing import TYPE_CHECKING, Any, List, Optional, Sequence, Tuple, Union

# import numpy as np
# from gym import spaces

# from habitat.config import read_write
# from habitat.config.default import get_agent_config
# from habitat.core.dataset import Dataset, Episode

# from habitat.core.logging import logger
# from habitat.core.registry import registry
# from habitat.tasks.rearrange.utils import UsesArticulatedAgentInterface
# from habitat.tasks.nav.nav import PointGoalSensor, Success
# from hydra.core.config_store import ConfigStore
# import habitat_sim
# from habitat.tasks.rearrange.rearrange_sensors import NumStepsMeasure
# from dataclasses import dataclass
# from habitat.config.default_structured_configs import MeasurementConfig

# from habitat.tasks.rearrange.utils import rearrange_collision
# from habitat.core.embodied_task import Measure
# from habitat.tasks.rearrange.social_nav.utils import (
#     robot_human_vec_dot_product,
# )
# from habitat.tasks.nav.nav import DistanceToGoalReward, DistanceToGoal
# from habitat.tasks.rearrange.utils import coll_name_matches
# try:
#     import magnum as mn
# except ImportError:
#     pass

# if TYPE_CHECKING:
#     from omegaconf import DictConfig


# @registry.register_measure
# class DidMultiAgentsCollide(Measure):
#     """
#     Detects if the multi-agent ( more than 1 humanoids agents) in the scene 
#     are colliding with each other at the current step. 
#     """

#     @staticmethod
#     def _get_uuid(*args, **kwargs):
#         return "did_multi_agents_collide"

#     def reset_metric(self, *args, **kwargs):
#         self.update_metric(
#             *args,
#             **kwargs,
#         )

#     def update_metric(self, *args, task, **kwargs):
#         sim = task._sim
#         human_num = task._human_num
#         sim.perform_discrete_collision_detection()
#         contact_points = sim.get_physics_contact_points()
#         found_contact = False

#         agent_ids = [
#             articulated_agent.sim_obj.object_id
#             for articulated_agent in sim.agents_mgr.articulated_agents_iter
#         ]
#         main_agent_id = agent_ids[0]
#         other_agent_ids = set(agent_ids[1:human_num+1])  
#         for cp in contact_points:
#             if coll_name_matches(cp, main_agent_id):
#                 if any(coll_name_matches(cp, agent_id) for agent_id in other_agent_ids):
#                     found_contact = True
#                     break  

#         self._metric = found_contact

# @registry.register_measure
# class HumanCollision(Measure):

#     cls_uuid: str = "human_collision"

#     def __init__(self, sim, config, *args, **kwargs):
#         self._sim = sim
#         self._config = config
#         self._ever_collide = False
#         super().__init__()

#     def _get_uuid(self, *args, **kwargs):
#         return self.cls_uuid

#     def reset_metric(self, *args, episode, task, observations, **kwargs):
#         task.measurements.check_measure_dependencies(
#             self.uuid, [DidMultiAgentsCollide._get_uuid()]
#         )
#         self._metric = 0.0
#         self._ever_collide = False

#     def update_metric(self, *args, episode, task, observations, **kwargs):
#         collid = task.measurements.measures[DidMultiAgentsCollide._get_uuid()].get_metric()
#         if collid or self._ever_collide:
#             self._metric = 1.0
#             self._ever_collide = True
#             task.should_end = True
#         else:
#             self._metric = 0.0

# @registry.register_measure
# class STL(Measure):
#     r"""Success weighted by Completion Time
#     """
#     cls_uuid: str = "stl"
    
#     def __init__(self, sim, config, *args, **kwargs):
#         self._sim = sim
#         self._config = config
#         super().__init__()

#     def _get_uuid(self, *args, **kwargs):
#         return self.cls_uuid

#     def reset_metric(self, *args, episode, task, observations, **kwargs):
#         task.measurements.check_measure_dependencies(
#             self.uuid, [DistanceToGoal.cls_uuid, Success.cls_uuid, NumStepsMeasure.cls_uuid]
#         )

#         self._num_steps_taken = 0
#         self._start_end_episode_distance = task.measurements.measures[
#             DistanceToGoal.cls_uuid
#         ].get_metric()
#         self.update_metric(episode=episode, task=task, observations=observations, *args, **kwargs)

#     def update_metric(self, *args, episode, task, observations, **kwargs):
#         ep_success = task.measurements.measures[Success.cls_uuid].get_metric() 
#         self._num_steps_taken = task.measurements.measures[NumStepsMeasure.cls_uuid].get_metric()

#         oracle_time = (
#             self._start_end_episode_distance / (0.25 / 10)
#         )
#         oracle_time = max(oracle_time, 1e-6)
#         agent_time = max(self._num_steps_taken, 1e-6)
#         self._metric = ep_success * (oracle_time / max(oracle_time, agent_time))

# @registry.register_measure
# class PersonalSpaceCompliance(Measure):

#     cls_uuid: str = "psc"

#     def __init__(self, sim, config, *args, **kwargs):
#         self._sim = sim
#         self._config = config
#         self._use_geo_distance = config.use_geo_distance
#         super().__init__()
        
#     def _get_uuid(self, *args, **kwargs):
#         return self.cls_uuid

#     def reset_metric(self, *args, episode, task, observations, **kwargs):
#         task.measurements.check_measure_dependencies(
#             self.uuid, [NumStepsMeasure.cls_uuid]
#         )
#         self._compliant_steps = 0
#         self._num_steps = 0

#     def update_metric(self, *args, episode, task, observations, **kwargs):
#         self._human_nums = min(episode.info['human_num'], self._sim.num_articulated_agents - 1)
#         if self._human_nums == 0:
#             self._metric = 1.0
#         else:
#             robot_pos = self._sim.get_agent_state(0).position
#             self._num_steps = task.measurements.measures[NumStepsMeasure.cls_uuid].get_metric()
#             compliance = True
#             for i in range(self._human_nums):
#                 human_position = self._sim.get_agent_state(i+1).position

#                 if self._use_geo_distance:
#                     path = habitat_sim.ShortestPath()
#                     path.requested_start = robot_pos
#                     path.requested_end = human_position
#                     found_path = self._sim.pathfinder.find_path(path)

#                     if found_path:
#                         distance = self._sim.geodesic_distance(robot_pos, human_position)
#                     else:
#                         distance = np.linalg.norm(human_position - robot_pos, ord=2)
#                 else:
#                     distance = np.linalg.norm(human_position - robot_pos, ord=2)

#                 if distance < 1.0:
#                     compliance = False
#                     break                    

#             if compliance:
#                 self._compliant_steps += 1
#             self._metric = (self._compliant_steps / self._num_steps)

# @registry.register_measure
# class MultiAgentNavReward(Measure):
#     """
#     Reward that gives a continuous reward for the social navigation task.
#     """

#     cls_uuid: str = "multi_agent_nav_reward"
        
#     # @staticmethod
#     # def _get_uuid(*args, **kwargs):
#     #     return MultiAgentNavReward.cls_uuid
#     def _get_uuid(self,*args, **kwargs):
#         return self.cls_uuid

#     def __init__(self, *args, **kwargs):
#         super().__init__(*args, **kwargs)
#         self._metric = 0.0
#         config = kwargs["config"]
#         # Get the config and setup the hyperparameters
#         self._config = config
#         self._sim = kwargs["sim"]

#         self._use_geo_distance = config.use_geo_distance
#         self._allow_distance = config.allow_distance
#         self._collide_scene_penalty = config.collide_scene_penalty
#         self._collide_human_penalty = config.collide_human_penalty
#         self._trajectory_cover_penalty = config.trajectory_cover_penalty
#         self._threshold_squared = config.cover_future_dis_thre ** 2
#         self._robot_idx = config.robot_idx
#         self._close_to_human_penalty = config.close_to_human_penalty
#         self._facing_human_dis = config.facing_human_dis

#         self._human_nums = 0

#     def reset_metric(self, *args, episode, task, observations, **kwargs):
#         if "human_num" in episode.info:
#             self._human_nums = min(episode.info['human_num'], self._sim.num_articulated_agents - 1)
#         else: 
#             self._human_nums = 0
#         self._metric = 0.0
        
#     def _check_human_facing_robot(self, human_pos, robot_pos, human_idx):
#         base_T = self._sim.get_agent_data(
#             human_idx
#         ).articulated_agent.sim_obj.transformation
#         facing = (
#             robot_human_vec_dot_product(human_pos, robot_pos, base_T)
#             > self._config.human_face_robot_threshold
#         )
#         return facing
    
#     def update_metric(self, *args, episode, task, observations, **kwargs):

#         # Start social nav reward
#         social_nav_reward = 0.0

#         # Component 1: Goal distance reward (strengthened by multiplying by 1.5)
#         distance_to_goal_reward = task.measurements.measures[
#             DistanceToGoalReward.cls_uuid
#         ].get_metric()
#         social_nav_reward += 1.5 * distance_to_goal_reward  # Slightly reduced reward multiplier

#         # Component 2: Penalize being too close to humans
#         distance_to_target = task.measurements.measures[
#             DistanceToGoal.cls_uuid
#         ].get_metric()
#         use_k_robot = f"agent_{self._robot_idx}_localization_sensor"
#         robot_pos = np.array(observations[use_k_robot][:3])

#         if distance_to_target > self._allow_distance:
#             human_dis = []
#             for i in range(self._human_nums):
#                 use_k_human = f"agent_{i+1}_localization_sensor"
#                 human_position = observations[use_k_human][:3]

#                 if self._use_geo_distance:
#                     path = habitat_sim.ShortestPath()
#                     path.requested_start = robot_pos
#                     path.requested_end = human_position
#                     found_path = self._sim.pathfinder.find_path(path)
#                     if found_path:
#                         distance = self._sim.geodesic_distance(robot_pos, human_position)
#                     else:
#                         distance = np.linalg.norm(human_position - robot_pos, ord=2)
#                 else:
#                     distance = np.linalg.norm(human_position - robot_pos, ord=2)
#                 human_dis.append(distance)
            
#             # Apply penalties for being too close to humans
#             for distance in human_dis:
#                 if distance < self._facing_human_dis:
#                     penalty = self._close_to_human_penalty * np.exp(-distance / self._facing_human_dis)
#                     social_nav_reward += penalty

#         # Component 3: Collision detection for two agents
#         did_agents_collide = task.measurements.measures[
#             DidMultiAgentsCollide._get_uuid()
#         ].get_metric()
#         if did_agents_collide:
#             task.should_end = True
#             social_nav_reward += self._collide_human_penalty

#         # Component 4: Collision detection for the main agent and the scene 
#         did_rearrange_collide, collision_detail = rearrange_collision(
#             self._sim, True, ignore_base=False, agent_idx=self._robot_idx
#         )
#         if did_rearrange_collide:
#             social_nav_reward += self._collide_scene_penalty
        
#         # Component 5: Trajectory overlap penalty with time-based weighting
#         if distance_to_target > self._allow_distance and "human_future_trajectory" in task.measurements.measures:
#             human_future_trajectory_temp = task.measurements.measures['human_future_trajectory']._metric
#             for trajectory in human_future_trajectory_temp.values():
#                 for t, point in enumerate(trajectory):
#                     time_weight = 1.0 / (1 + t)  # Time-weighted penalty
#                     if np.sum((robot_pos - point) ** 2) < self._threshold_squared:
#                         social_nav_reward += self._trajectory_cover_penalty * time_weight
#                         break

#         self._metric = social_nav_reward

# @registry.register_measure
# class HumanVelocityMeasure(UsesArticulatedAgentInterface, Measure):
#     """
#     The measure for ORCA
#     """

#     cls_uuid: str = "human_velocity_measure"

#     def __init__(self, *args, sim, **kwargs):
#         self._sim = sim
#         self.human_num = kwargs['task']._human_num
#         self.velo_coff = np.array([[0, 1]] * 6)
#         self.velo_base = np.array([[0.25, np.deg2rad(10)]] * 6)
        
#         super().__init__(*args, sim=sim, **kwargs)
#         self._metric = self.velo_base * self.velo_coff 

#     @staticmethod
#     def _get_uuid(*args, **kwargs):
#         return HumanVelocityMeasure.cls_uuid

#     def reset_metric(self, *args, episode, task, observations, **kwargs):
#         self.human_num = task._human_num
#         self.velo_coff = np.array([[0.0, 0.0]] * 6)
#         self.velo_base = np.array([[0.25, np.deg2rad(10)]] * 6)
#         self._metric = self.velo_base * self.velo_coff 

#     def update_metric(self, *args, episode, task, observations, **kwargs):
#         self._metric = self.velo_base * self.velo_coff 

# def merge_paths(paths):
#     merged_path = []
#     for i, path in enumerate(paths):
#         if i > 0:
#             path = path[1:]
#         merged_path.extend(path)
#     return merged_path


# @registry.register_measure
# class HumanFutureTrajectory(UsesArticulatedAgentInterface, Measure):
#     """
#     The measure for future prediction of social crowd navigation
#     """

#     cls_uuid: str = "human_future_trajectory"

#     def __init__(self, *args, sim, **kwargs):
#         self._sim = sim
#         self.num_agents = sim.num_articulated_agents
#         self.target_dict = [[[0, 0, 0]] for _ in range(self.num_agents-1)]
#         self.path_dict = {}
#         super().__init__(*args, sim=sim, **kwargs)

#     @staticmethod
#     def _get_uuid(*args, **kwargs):
#         return HumanFutureTrajectory.cls_uuid

#     def reset_metric(self, *args, episode, task, observations, **kwargs):
#         self.update_metric(
#             *args,
#             episode=episode,
#             task=task,
#             observations=observations,
#             **kwargs,
#         )

#     def _path_to_point(self, point_a,point_b):

#         path = habitat_sim.ShortestPath()
#         path.requested_start = point_a 
#         path.requested_end = point_b
#         found_path = self._sim.pathfinder.find_path(path)
#         if not found_path:
#             return [point_a, point_b]
#         return path.points

#     def update_metric(self, *args, episode, task, observations, **kwargs):
#         for agent_idx, target in enumerate(self.target_dict):
#             path = []
            
#             agent_pos = self._sim.get_agent_data(agent_idx+1).articulated_agent.base_pos
#             for i in range(-1,len(target)):
#                 if i == -1:
#                     path_point = np.array(agent_pos)
#                 else:
#                     path_point = target[i]

#                 if i >= 0:
#                     temp_path = self._path_to_point(prev_point, path_point)
#                     path.append(temp_path)
                
#                 prev_point = path_point

#             if path == []:
#                 self.path_dict[agent_idx + 1] = []
#             else:
#                 temp_merged_path = merge_paths(path)
#                 output_length = min(5, len(temp_merged_path))
#                 self.path_dict[agent_idx + 1] = temp_merged_path[:output_length]

#         self._metric = self.path_dict

# @registry.register_measure
# class HumanFutureTrajectory(UsesArticulatedAgentInterface, Measure):
#     """
#     The measure for future prediction of social crowd navigation.
#     """

#     cls_uuid: str = "human_future_trajectory"

#     def __init__(self, *args, sim, **kwargs):
#         self._sim = sim
#         self.human_num = kwargs['task']._human_num
#         self.output_length = 5
#         self.target_dict = self._initialize_target_dict(self.human_num)
#         self.path_dict = {}
#         super().__init__(*args, sim=sim, **kwargs)

#     @staticmethod
#     def _get_uuid(*args, **kwargs):
#         return HumanFutureTrajectory.cls_uuid

#     def _initialize_target_dict(self, human_num):
#         """Initialize the target dictionary with default values."""
#         return np.full((human_num, 2, 3), -100, dtype=np.float32).tolist()

#     def reset_metric(self, *args, episode, task, observations, **kwargs):
#         self.human_num = task._human_num
#         self.target_dict = self._initialize_target_dict(self.human_num)
#         self.path_dict = {}
#         self._metric = {}

#     def _path_to_point(self, point_a, point_b):
#         """Get the shortest path between two points."""
#         path = habitat_sim.ShortestPath()  
#         path.requested_start = point_a 
#         path.requested_end = point_b
#         found_path = self._sim.pathfinder.find_path(path)
#         return path.points if found_path else [point_a, point_b]

#     def _process_path(self, path):
#         """Process the path by merging and padding/truncating to the desired length."""
#         temp_merged_path = merge_paths(path)
        
#         if len(temp_merged_path) < self.output_length:
#             padding = np.full((self.output_length - len(temp_merged_path), 3), temp_merged_path[-1], dtype=np.float32)
#             temp_merged_path = np.concatenate([temp_merged_path, padding], axis=0)
#         else:
#             temp_merged_path = np.array(temp_merged_path[:self.output_length], dtype=np.float32)
        
#         return temp_merged_path.tolist()

#     def update_metric(self, *args, episode, task, observations, **kwargs):
#         for agent_idx, target in enumerate(self.target_dict):
#             path = []
#             agent_pos = np.array(self._sim.get_agent_data(agent_idx + 1).articulated_agent.base_pos)

#             prev_point = agent_pos
#             for i in range(len(target)):
#                 path_point = np.array(target[i])
#                 temp_path = self._path_to_point(prev_point, path_point)
#                 path.append(temp_path)
#                 prev_point = path_point

#             self.path_dict[agent_idx + 1] = self._process_path(path)
            
#         self._metric = self.path_dict

# @dataclass
# class MultiAgentNavReward(MeasurementConfig):
#     r"""
#     The reward for the multi agent navigation tasks.
#     """
#     type: str = "MultiAgentNavReward"
    
#     # If we want to use geo distance to measure the distance
#     # between the robot and the human
#     use_geo_distance: bool = True
#     # discomfort for multi agents
#     allow_distance: float = 0.5 
#     collide_scene_penalty: float = -0.25 
#     collide_human_penalty: float = -0.5  
#     facing_human_dis: float = 1.0
#     human_face_robot_threshold: float = 0.5
#     close_to_human_penalty: float = -0.025
#     trajectory_cover_penalty: float = -0.025 
#     cover_future_dis_thre: float = -0.05  
#     # Set the id of the agent
#     robot_idx: int = 0

# @dataclass
# class DidMultiAgentsCollideConfig(MeasurementConfig):
#     type: str = "DidMultiAgentsCollide"
    
# @dataclass
# class STLMeasurementConfig(MeasurementConfig):
#     type: str = "STL"

# @dataclass
# class PersonalSpaceComplianceMeasurementConfig(MeasurementConfig):
#     type: str = "PersonalSpaceCompliance"
#     use_geo_distance: bool = True
    
# @dataclass
# class HumanCollisionMeasurementConfig(MeasurementConfig):
#     type: str = "HumanCollision"

# @dataclass
# class HumanVelocityMeasurementConfig(MeasurementConfig):
#     type: str = "HumanVelocityMeasure"

# @dataclass
# class HumanFutureTrajectoryMeasurementConfig(MeasurementConfig):
#     type: str = "HumanFutureTrajectory"


# cs = ConfigStore.instance()

# cs.store(
#     package="habitat.task.measurements.multi_agent_nav_reward",
#     group="habitat/task/measurements",
#     name="multi_agent_nav_reward",
#     node=MultiAgentNavReward,
# )
# cs.store(
#     package="habitat.task.measurements.stl",
#     group="habitat/task/measurements",
#     name="stl",
#     node=STLMeasurementConfig,
# )
# cs.store(
#     package="habitat.task.measurements.psc",
#     group="habitat/task/measurements",
#     name="psc",
#     node=PersonalSpaceComplianceMeasurementConfig,
# )
# cs.store(
#     package="habitat.task.measurements.human_collision",
#     group="habitat/task/measurements",
#     name="human_collision",
#     node=HumanCollisionMeasurementConfig,
# )
# cs.store(
#     package="habitat.task.measurements.did_multi_agents_collide",
#     group="habitat/task/measurements",
#     name="did_multi_agents_collide",
#     node=DidMultiAgentsCollideConfig,
# )
# cs.store(
#     package="habitat.task.measurements.human_velocity_measure",
#     group="habitat/task/measurements",
#     name="human_velocity_measure",
#     node=HumanVelocityMeasurementConfig,
# )
# cs.store(
#     package="habitat.task.measurements.human_future_trajectory",
#     group="habitat/task/measurements",
#     name="human_future_trajectory",
#     node=HumanFutureTrajectoryMeasurementConfig,
# )
#-----------------------Old Code（没有密度机制）----------------------------

#-----------------------New Code------------------------------------------
# #!/usr/bin/env python3

# # This source code is licensed under the MIT license found in the
# # LICENSE file in the root directory of this source tree.


from typing import TYPE_CHECKING, Any, List, Optional, Sequence, Tuple, Union

import numpy as np
from gym import spaces

from habitat.config import read_write
from habitat.config.default import get_agent_config
from habitat.core.dataset import Dataset, Episode

from habitat.core.logging import logger
from habitat.core.registry import registry
from habitat.tasks.rearrange.utils import UsesArticulatedAgentInterface
from habitat.tasks.nav.nav import PointGoalSensor, Success
from hydra.core.config_store import ConfigStore
import habitat_sim
from habitat.tasks.rearrange.rearrange_sensors import NumStepsMeasure
from dataclasses import dataclass
from habitat.config.default_structured_configs import MeasurementConfig

from habitat.tasks.rearrange.utils import rearrange_collision
from habitat.core.embodied_task import Measure
from habitat.tasks.rearrange.social_nav.utils import (
    robot_human_vec_dot_product,
)
from habitat.tasks.nav.nav import DistanceToGoalReward, DistanceToGoal
from habitat.tasks.rearrange.utils import coll_name_matches
try:
    import magnum as mn
except ImportError:
    pass

if TYPE_CHECKING:
    from omegaconf import DictConfig


@registry.register_measure
class DidMultiAgentsCollide(Measure):
    """
    Detects if the multi-agent ( more than 1 humanoids agents) in the scene 
    are colliding with each other at the current step. 
    """

    @staticmethod
    def _get_uuid(*args, **kwargs):
        return "did_multi_agents_collide"

    def reset_metric(self, *args, **kwargs):
        self.update_metric(
            *args,
            **kwargs,
        )

    def update_metric(self, *args, task, **kwargs):
        sim = task._sim
        human_num = task._human_num
        sim.perform_discrete_collision_detection()
        contact_points = sim.get_physics_contact_points()
        found_contact = False

        agent_ids = [
            articulated_agent.sim_obj.object_id
            for articulated_agent in sim.agents_mgr.articulated_agents_iter
        ]
        main_agent_id = agent_ids[0]
        other_agent_ids = set(agent_ids[1:human_num+1])  
        for cp in contact_points:
            if coll_name_matches(cp, main_agent_id):
                if any(coll_name_matches(cp, agent_id) for agent_id in other_agent_ids):
                    found_contact = True
                    break  

        self._metric = found_contact

@registry.register_measure
class HumanCollision(Measure):

    cls_uuid: str = "human_collision"

    def __init__(self, sim, config, *args, **kwargs):
        self._sim = sim
        self._config = config
        self._ever_collide = False
        super().__init__()

    def _get_uuid(self, *args, **kwargs):
        return self.cls_uuid

    def reset_metric(self, *args, episode, task, observations, **kwargs):
        task.measurements.check_measure_dependencies(
            self.uuid, [DidMultiAgentsCollide._get_uuid()]
        )
        self._metric = 0.0
        self._ever_collide = False

    def update_metric(self, *args, episode, task, observations, **kwargs):
        collid = task.measurements.measures[DidMultiAgentsCollide._get_uuid()].get_metric()
        if collid or self._ever_collide:
            self._metric = 1.0
            self._ever_collide = True
            task.should_end = True
        else:
            self._metric = 0.0

@registry.register_measure
class STL(Measure):
    r"""Success weighted by Completion Time
    """
    cls_uuid: str = "stl"
    
    def __init__(self, sim, config, *args, **kwargs):
        self._sim = sim
        self._config = config
        super().__init__()

    def _get_uuid(self, *args, **kwargs):
        return self.cls_uuid

    def reset_metric(self, *args, episode, task, observations, **kwargs):
        task.measurements.check_measure_dependencies(
            self.uuid, [DistanceToGoal.cls_uuid, Success.cls_uuid, NumStepsMeasure.cls_uuid]
        )

        self._num_steps_taken = 0
        self._start_end_episode_distance = task.measurements.measures[
            DistanceToGoal.cls_uuid
        ].get_metric()
        self.update_metric(episode=episode, task=task, observations=observations, *args, **kwargs)

    def update_metric(self, *args, episode, task, observations, **kwargs):
        ep_success = task.measurements.measures[Success.cls_uuid].get_metric() 
        self._num_steps_taken = task.measurements.measures[NumStepsMeasure.cls_uuid].get_metric()

        oracle_time = (
            self._start_end_episode_distance / (0.25 / 10)
        )
        oracle_time = max(oracle_time, 1e-6)
        agent_time = max(self._num_steps_taken, 1e-6)
        self._metric = ep_success * (oracle_time / max(oracle_time, agent_time))

@registry.register_measure
class PersonalSpaceCompliance(Measure):

    cls_uuid: str = "psc"

    def __init__(self, sim, config, *args, **kwargs):
        self._sim = sim
        self._config = config
        self._use_geo_distance = config.use_geo_distance
        super().__init__()
        
    def _get_uuid(self, *args, **kwargs):
        return self.cls_uuid

    def reset_metric(self, *args, episode, task, observations, **kwargs):
        task.measurements.check_measure_dependencies(
            self.uuid, [NumStepsMeasure.cls_uuid]
        )
        self._compliant_steps = 0
        self._num_steps = 0

    def update_metric(self, *args, episode, task, observations, **kwargs):
        self._human_nums = min(episode.info['human_num'], self._sim.num_articulated_agents - 1)
        if self._human_nums == 0:
            self._metric = 1.0
        else:
            robot_pos = self._sim.get_agent_state(0).position
            self._num_steps = task.measurements.measures[NumStepsMeasure.cls_uuid].get_metric()
            compliance = True
            for i in range(self._human_nums):
                human_position = self._sim.get_agent_state(i+1).position # 算环境中每一个人的位置

                if self._use_geo_distance:
                    path = habitat_sim.ShortestPath()
                    path.requested_start = robot_pos
                    path.requested_end = human_position
                    found_path = self._sim.pathfinder.find_path(path)

                    if found_path:
                        distance = self._sim.geodesic_distance(robot_pos, human_position)
                    else:
                        distance = np.linalg.norm(human_position - robot_pos, ord=2)
                else:
                    distance = np.linalg.norm(human_position - robot_pos, ord=2)

                if distance < 1.0:
                    compliance = False # 保持距离不足
                    break                    

            if compliance:
                self._compliant_steps += 1
            self._metric = (self._compliant_steps / self._num_steps) # PSC 整个运行过程中，有多少比例的steps保持了社交距离；越高越礼让

@registry.register_measure
class MultiAgentNavReward(Measure):
    """
    Reward that gives a continuous reward for the social navigation task. 总奖励！！
    """

    cls_uuid: str = "multi_agent_nav_reward"
        
    # @staticmethod
    # def _get_uuid(*args, **kwargs):
    #     return MultiAgentNavReward.cls_uuid
    def _get_uuid(self,*args, **kwargs):
        return self.cls_uuid

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._metric = 0.0
        config = kwargs["config"]
        # Get the config and setup the hyperparameters
        self._config = config
        self._sim = kwargs["sim"]

        self._use_geo_distance = config.use_geo_distance 
        self._allow_distance = config.allow_distance # 距离目标小于这个值时不计算人距离惩罚
        # density-based modulation hyperparams (can be tuned in config)
        # sigma for Gaussian kernel when computing local density (meters)
        self._density_sigma = getattr(config, "density_sigma", 1.0)
        # how strongly density reduces goal reward (0=no effect, larger=stronger)
        self._density_goal_alpha = getattr(config, "density_goal_alpha", 0.5)
        # how strongly density increases human-related penalties (0=no effect, larger=stronger)
        self._density_penalty_beta = getattr(config, "density_penalty_beta", 0.5)
        # min allowed value for allow_distance after shrink
        self._allow_distance_min = getattr(config, "allow_distance_min", 0.1)
        # fraction to shrink allow_distance at max density (0=no shrink, 1=shrink to min)
        self._allow_distance_shrink = getattr(config, "allow_distance_shrink", 0.5)
        # 碰撞惩罚
        self._collide_scene_penalty = config.collide_scene_penalty
        self._collide_human_penalty = config.collide_human_penalty
        self._trajectory_cover_penalty = config.trajectory_cover_penalty # 挡住他人未来轨迹惩罚
        self._threshold_squared = config.cover_future_dis_thre ** 2
        self._robot_idx = config.robot_idx
        self._close_to_human_penalty = config.close_to_human_penalty
        self._facing_human_dis = config.facing_human_dis

        self._human_nums = 0

        #抑制模型原地转圈等
        self._path_overlap_penalty = getattr(config, "path_overlap_penalty", 0.0)
        self._path_overlap_thre = getattr(config, "path_overlap_thre", 0.5)
        self._path_overlap_thre_sq = self._path_overlap_thre ** 2
        self._path_history_len = getattr(config, "path_history_len", 50)
        self._path_recent_ignore = getattr(config, "path_recent_ignore", 3)

    def reset_metric(self, *args, episode, task, observations, **kwargs):
        if "human_num" in episode.info:
            self._human_nums = min(episode.info['human_num'], self._sim.num_articulated_agents - 1)
        else: 
            self._human_nums = 0
        self._metric = 0.0

        self._path_history = []
        
    def _check_human_facing_robot(self, human_pos, robot_pos, human_idx):
        base_T = self._sim.get_agent_data(
            human_idx
        ).articulated_agent.sim_obj.transformation
        facing = (
            robot_human_vec_dot_product(human_pos, robot_pos, base_T)
            > self._config.human_face_robot_threshold
        )
        return facing
    
    def update_metric(self, *args, episode, task, observations, **kwargs):

        social_nav_reward = 0.0

        # Component 0: compute a continuous local density metric from humans   
        # Use a Gaussian kernel on euclidean distances; normalized via 1-exp(-sum)
        distance_to_target = task.measurements.measures[                 
            DistanceToGoal.cls_uuid
        ].get_metric()
        use_k_robot = f"agent_{self._robot_idx}_localization_sensor"
        robot_pos = np.array(observations[use_k_robot][:3])

        ###关于轨迹重叠的惩罚###
        try:
            # append current position
            self._path_history.append(np.array(robot_pos, dtype=np.float32))
        except Exception:
            # if observations malformed, skip
            pass
        # trim history
        if len(self._path_history) > self._path_history_len:
            self._path_history = self._path_history[-self._path_history_len:]

        # check overlap with past path (ignore the most recent few points)
        if (
            self._path_overlap_penalty != 0.0
            and len(self._path_history) > self._path_recent_ignore
        ):
            past_points = np.array(self._path_history[:-self._path_recent_ignore])
            if past_points.size > 0:
                # compute squared distances to all past points
                d2 = np.sum((past_points - robot_pos) ** 2, axis=1)
                if np.any(d2 < self._path_overlap_thre_sq):
                    social_nav_reward += -abs(self._path_overlap_penalty)
        ######

        
        ###增加方向对齐奖励
        pointgoal_obs = observations["agent_0_pointgoal_with_gps_compass"]  # 假设使用 pointgoal
        phi = pointgoal_obs[1]  # 目标在机器人前方的角度（-pi ~ pi）
        angle_diff = np.abs(phi)
        heading_reward = -0.001 * angle_diff  # 可调系数
        social_nav_reward += heading_reward
        ######


        # Gather human distances (always compute density regardless of allow_distance)
        human_dis = []
        for i in range(self._human_nums):  # 遍历空间中所有的人
            use_k_human = f"agent_{i+1}_localization_sensor"
            human_position = observations[use_k_human][:3]

            if self._use_geo_distance:
                path = habitat_sim.ShortestPath()
                path.requested_start = robot_pos
                path.requested_end = human_position
                found_path = self._sim.pathfinder.find_path(path)
                if found_path:
                    distance = self._sim.geodesic_distance(robot_pos, human_position)
                else:
                    distance = np.linalg.norm(human_position - robot_pos, ord=2)
            else:
                distance = np.linalg.norm(human_position - robot_pos, ord=2)
            human_dis.append(distance)

        # Compute Gaussian-kernel-based local density
        density_raw = 0.0                                                                         ###   基于密度的有关参数计算
        for d in human_dis:
            # use squared Gaussian kernel so nearer humans contribute more
            density_raw += np.exp(-(d * d) / (2.0 * (self._density_sigma ** 2) + 1e-9))

        # normalized density in (0, 1): 1 - exp(-density_raw)
        density = 0.0
        if density_raw > 0:
            density = 1.0 - np.exp(-density_raw)

        # Effective allow_distance shrinks with density (more conservative when crowded)
        allow_distance_eff = max(                          ### 基于密度的允许距离调整：
            self._allow_distance_min,
            self._allow_distance * (1.0 - self._allow_distance_shrink * density),
        )

        # Component 1: Goal distance reward (strengthened by multiplying by 1.5)
        # 11.20 modify back: 局部密度不影响这个goal_weight，只动增大下面的惩罚; 即 人多需要更注意避让，但是也还是鼓励往目标走
        distance_to_goal_reward = task.measurements.measures[
            DistanceToGoalReward.cls_uuid
        ].get_metric()
        social_nav_reward += 1.5 * distance_to_goal_reward # 11.20 modify back: 局部密度不影响这个goal_weight，只动增大下面的惩罚; 即 人多需要更注意避让，但是也还是鼓励往目标走

        # # Component 1: Goal distance reward (modulate by density: less weight when crowded)
        # distance_to_goal_reward = task.measurements.measures[
        #     DistanceToGoalReward.cls_uuid
        # ].get_metric()
        # goal_weight = 1.5 * max(0.0, 1.0 - self._density_goal_alpha * density)       ### 基于密度的目标距离奖励调节
        # social_nav_reward += goal_weight * distance_to_goal_reward

        # Component 2: Penalize being too close to humans (scale penalty by density)
        if distance_to_target > allow_distance_eff:  # 仅在离目标较远时惩罚；快到终点了鼓励“冲刺”
            for distance in human_dis:
                if distance < self._facing_human_dis:
                    base_pen = self._close_to_human_penalty * np.exp(-distance / self._facing_human_dis)
                    penalty = base_pen * (1.0 + self._density_penalty_beta * density)     ### 基于密度的接近人类惩罚调节
                    social_nav_reward += penalty

        # Component 3: Collision detection for two agents
        did_agents_collide = task.measurements.measures[
            DidMultiAgentsCollide._get_uuid()
        ].get_metric()
        if did_agents_collide:
            task.should_end = True
            social_nav_reward += self._collide_human_penalty

        # Component 4: Collision detection for the main agent and the scene 
        did_rearrange_collide, collision_detail = rearrange_collision(
            self._sim, True, ignore_base=False, agent_idx=self._robot_idx
        )
        if did_rearrange_collide:
            social_nav_reward += self._collide_scene_penalty
        
        # Component 5: Trajectory overlap penalty with time-based weighting
        if distance_to_target > self._allow_distance and "human_future_trajectory" in task.measurements.measures:
            human_future_trajectory_temp = task.measurements.measures['human_future_trajectory']._metric
            for trajectory in human_future_trajectory_temp.values():
                for t, point in enumerate(trajectory):
                    time_weight = 1.0 / (1 + t)  # Time-weighted penalty
                    if np.sum((robot_pos - point) ** 2) < self._threshold_squared:
                        social_nav_reward += self._trajectory_cover_penalty * time_weight
                        break

        self._metric = social_nav_reward

@registry.register_measure
class HumanVelocityMeasure(UsesArticulatedAgentInterface, Measure):
    """
    The measure for ORCA
    """

    cls_uuid: str = "human_velocity_measure"

    def __init__(self, *args, sim, **kwargs):
        self._sim = sim
        self.human_num = kwargs['task']._human_num
        self.velo_coff = np.array([[0, 1]] * 6)
        self.velo_base = np.array([[0.25, np.deg2rad(10)]] * 6)
        
        super().__init__(*args, sim=sim, **kwargs)
        self._metric = self.velo_base * self.velo_coff 

    @staticmethod
    def _get_uuid(*args, **kwargs):
        return HumanVelocityMeasure.cls_uuid

    def reset_metric(self, *args, episode, task, observations, **kwargs):
        self.human_num = task._human_num
        self.velo_coff = np.array([[0.0, 0.0]] * 6)
        self.velo_base = np.array([[0.25, np.deg2rad(10)]] * 6)
        self._metric = self.velo_base * self.velo_coff 

    def update_metric(self, *args, episode, task, observations, **kwargs):
        self._metric = self.velo_base * self.velo_coff 

def merge_paths(paths):
    merged_path = []
    for i, path in enumerate(paths):
        if i > 0:
            path = path[1:]
        merged_path.extend(path)
    return merged_path


@registry.register_measure
class HumanFutureTrajectory(UsesArticulatedAgentInterface, Measure):
    """
    The measure for future prediction of social crowd navigation
    """

    cls_uuid: str = "human_future_trajectory"

    def __init__(self, *args, sim, **kwargs):
        self._sim = sim
        self.num_agents = sim.num_articulated_agents
        self.target_dict = [[[0, 0, 0]] for _ in range(self.num_agents-1)]
        self.path_dict = {}
        super().__init__(*args, sim=sim, **kwargs)

    @staticmethod
    def _get_uuid(*args, **kwargs):
        return HumanFutureTrajectory.cls_uuid

    def reset_metric(self, *args, episode, task, observations, **kwargs):
        self.update_metric(
            *args,
            episode=episode,
            task=task,
            observations=observations,
            **kwargs,
        )

    def _path_to_point(self, point_a,point_b):

        path = habitat_sim.ShortestPath()
        path.requested_start = point_a 
        path.requested_end = point_b
        found_path = self._sim.pathfinder.find_path(path)
        if not found_path:
            return [point_a, point_b]
        return path.points

    def update_metric(self, *args, episode, task, observations, **kwargs):
        for agent_idx, target in enumerate(self.target_dict):
            path = []
            
            agent_pos = self._sim.get_agent_data(agent_idx+1).articulated_agent.base_pos
            for i in range(-1,len(target)):
                if i == -1:
                    path_point = np.array(agent_pos)
                else:
                    path_point = target[i]

                if i >= 0:
                    temp_path = self._path_to_point(prev_point, path_point)
                    path.append(temp_path)
                
                prev_point = path_point

            if path == []:
                self.path_dict[agent_idx + 1] = []
            else:
                temp_merged_path = merge_paths(path)
                output_length = min(5, len(temp_merged_path))
                self.path_dict[agent_idx + 1] = temp_merged_path[:output_length]

        self._metric = self.path_dict

@registry.register_measure
class HumanFutureTrajectory(UsesArticulatedAgentInterface, Measure):
    """
    The measure for future prediction of social crowd navigation.
    """

    cls_uuid: str = "human_future_trajectory"

    def __init__(self, *args, sim, **kwargs):
        self._sim = sim
        self.human_num = kwargs['task']._human_num
        self.output_length = 5
        self.target_dict = self._initialize_target_dict(self.human_num)
        self.path_dict = {}
        super().__init__(*args, sim=sim, **kwargs)

    @staticmethod
    def _get_uuid(*args, **kwargs):
        return HumanFutureTrajectory.cls_uuid

    def _initialize_target_dict(self, human_num):
        """Initialize the target dictionary with default values."""
        return np.full((human_num, 2, 3), -100, dtype=np.float32).tolist()

    def reset_metric(self, *args, episode, task, observations, **kwargs):
        self.human_num = task._human_num
        self.target_dict = self._initialize_target_dict(self.human_num)
        self.path_dict = {}
        self._metric = {}

    def _path_to_point(self, point_a, point_b):
        """Get the shortest path between two points."""
        path = habitat_sim.ShortestPath()  
        path.requested_start = point_a 
        path.requested_end = point_b
        found_path = self._sim.pathfinder.find_path(path)
        return path.points if found_path else [point_a, point_b]

    def _process_path(self, path):
        """Process the path by merging and padding/truncating to the desired length."""
        temp_merged_path = merge_paths(path)
        
        if len(temp_merged_path) < self.output_length:
            padding = np.full((self.output_length - len(temp_merged_path), 3), temp_merged_path[-1], dtype=np.float32)
            temp_merged_path = np.concatenate([temp_merged_path, padding], axis=0)
        else:
            temp_merged_path = np.array(temp_merged_path[:self.output_length], dtype=np.float32)
        
        return temp_merged_path.tolist()

    def update_metric(self, *args, episode, task, observations, **kwargs):
        for agent_idx, target in enumerate(self.target_dict):
            path = []
            agent_pos = np.array(self._sim.get_agent_data(agent_idx + 1).articulated_agent.base_pos)

            prev_point = agent_pos
            for i in range(len(target)):
                path_point = np.array(target[i])
                temp_path = self._path_to_point(prev_point, path_point)
                path.append(temp_path)
                prev_point = path_point

            self.path_dict[agent_idx + 1] = self._process_path(path)
            
        self._metric = self.path_dict

@dataclass
class MultiAgentNavReward(MeasurementConfig):
    r"""
    The reward for the multi agent navigation tasks.
    """
    type: str = "MultiAgentNavReward"
    
    # If we want to use geo distance to measure the distance
    # between the robot and the human
    use_geo_distance: bool = True
    # discomfort for multi agents
    allow_distance: float = 0.5 
    collide_scene_penalty: float = -0.25 
    collide_human_penalty: float = -0.5  
    facing_human_dis: float = 1.0
    human_face_robot_threshold: float = 0.5
    close_to_human_penalty: float = -0.025
    trajectory_cover_penalty: float = -0.025 
    cover_future_dis_thre: float = -0.05  
    # Set the id of the agent
    
    # density modulation params (new)
    density_sigma: float = 1.0
    density_goal_alpha: float = 0.5
    density_penalty_beta: float = 0.5
    allow_distance_min: float = 0.1
    allow_distance_shrink: float = 0.5
    
    # Set the id of the agent
    robot_idx: int = 0

    ### Path overlap penalty params (new)
    path_overlap_penalty: float = -0.006 # -0.003
    path_overlap_thre: float = 0.5
    path_history_len: int = 50
    path_recent_ignore: int = 3   

@dataclass
class DidMultiAgentsCollideConfig(MeasurementConfig):
    type: str = "DidMultiAgentsCollide"
    
@dataclass
class STLMeasurementConfig(MeasurementConfig):
    type: str = "STL"

@dataclass
class PersonalSpaceComplianceMeasurementConfig(MeasurementConfig):
    type: str = "PersonalSpaceCompliance"
    use_geo_distance: bool = True
    
@dataclass
class HumanCollisionMeasurementConfig(MeasurementConfig):
    type: str = "HumanCollision"

@dataclass
class HumanVelocityMeasurementConfig(MeasurementConfig):
    type: str = "HumanVelocityMeasure"

@dataclass
class HumanFutureTrajectoryMeasurementConfig(MeasurementConfig):
    type: str = "HumanFutureTrajectory"


cs = ConfigStore.instance()

cs.store(
    package="habitat.task.measurements.multi_agent_nav_reward",
    group="habitat/task/measurements",
    name="multi_agent_nav_reward",
    node=MultiAgentNavReward,
)
cs.store(
    package="habitat.task.measurements.stl",
    group="habitat/task/measurements",
    name="stl",
    node=STLMeasurementConfig,
)
cs.store(
    package="habitat.task.measurements.psc",
    group="habitat/task/measurements",
    name="psc",
    node=PersonalSpaceComplianceMeasurementConfig,
)
cs.store(
    package="habitat.task.measurements.human_collision",
    group="habitat/task/measurements",
    name="human_collision",
    node=HumanCollisionMeasurementConfig,
)
cs.store(
    package="habitat.task.measurements.did_multi_agents_collide",
    group="habitat/task/measurements",
    name="did_multi_agents_collide",
    node=DidMultiAgentsCollideConfig,
)
cs.store(
    package="habitat.task.measurements.human_velocity_measure",
    group="habitat/task/measurements",
    name="human_velocity_measure",
    node=HumanVelocityMeasurementConfig,
)
cs.store(
    package="habitat.task.measurements.human_future_trajectory",
    group="habitat/task/measurements",
    name="human_future_trajectory",
    node=HumanFutureTrajectoryMeasurementConfig,
)