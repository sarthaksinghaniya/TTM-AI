"""JSON Serialization and Deserialization for SchedulingInstance."""

from brain.problem.scheduling_instance import SchedulingInstance


class InstanceSerializer:
    """Serializer handling JSON round-trips for a SchedulingInstance."""

    def serialize(self, instance: SchedulingInstance) -> str:
        """Serialize a SchedulingInstance to a JSON string.

        Args:
            instance: The SchedulingInstance.

        Returns:
            JSON string representation.
        """
        return instance.to_json()

    def deserialize(self, data: str) -> SchedulingInstance:
        """Deserialize a JSON string to a SchedulingInstance.

        Args:
            data: JSON string.

        Returns:
            A SchedulingInstance instance.
        """
        return SchedulingInstance.from_json(data)
