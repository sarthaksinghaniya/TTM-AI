class VariableEncoder:

    @staticmethod
    def assignment(
        lecture_id: str,
        room_id: str,
        slot_id: str,
    ) -> str:
        return f"A_L{lecture_id}_R{room_id}_S{slot_id}"

    @staticmethod
    def room(
        lecture_id: str,
        room_id: str,
    ) -> str:
        return f"R_L{lecture_id}_R{room_id}"

    @staticmethod
    def slot(
        lecture_id: str,
        slot_id: str,
    ) -> str:
        return f"S_L{lecture_id}_S{slot_id}"

    @staticmethod
    def interval(
        lecture_id: str,
    ) -> str:
        return f"I_L{lecture_id}"

    @staticmethod
    def integer(name: str) -> str:
        return f"N_{name}"

    @staticmethod
    def boolean(name: str) -> str:
        return f"B_{name}"