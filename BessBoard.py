from __future__ import annotations

import chess
import copy
import itertools
import dataclasses

from typing import Dict, Generic, Hashable, Iterable, Iterator, List, Optional, Type, TypeVar, Union

@dataclasses.dataclass(unsafe_hash=True)
class BessMove:
	from_square: chess.Square

	to_square: chess.Square

	ban_piece: chess.PieceType

	promotion: Optional[chess.PieceType] = None

	drop: Optional[chess.PieceType] = None

	def uci(self) -> str:
		"""
		Gets a UCI string for the move.

		For example, a move from a7 to a8 that bans knight moves would be ``a7a8:n`` or ``a7a8q:n``
		The latter is a promotion to a queen.

		The UCI representation of a null move is ``0000``.
		"""
		if self.move.promotion:
			return chess.SQUARE_NAMES[self.move.from_square] + chess.SQUARE_NAMES[self.move.to_square] + chess.piece_symbol(self.move.promotion) + ":" + chess.piece_symbol(self.ban_piece)
		elif self:
			return chess.SQUARE_NAMES[self.move.from_square] + chess.SQUARE_NAMES[self.move.to_square] + ":" + chess.piece_symbol(self.ban_piece)
		else:
			return "0000"

	def __bool__(self) -> bool:
		return bool(self.from_square or self.to_square or self.promotion or self.ban_piece)

	def __repr__(self) -> str:
		return f"Bess_Move.from_uci({self.uci()!r})"

	def __str__(self) -> str:
		return self.uci()

	def move(self) -> chess.Move:
		return chess.Move(self.from_square, self.to_square, promotion=self.promotion)

	@classmethod
	def from_uci(cls, uci: str) -> BessMove:
		"""
		Parses a UCI string. 

		:raises: :exec:`InvalidMoveError` if the UCI string is invalid.
		"""

		if uci == "0000":
			return cls.null()
		elif len(uci) == 6 and ":" == uci[5]:
			try:
				from_square = chess.SQUARE_NAMES.index(uci[0:2])
				to_square = chess.SQUARE_NAMES.index(uci[2:4])
				ban_piece = chess.PIECE_SYMBOLS.index(uci[6])
			except ValueError:
				raise chess.InvalidMoveError(f"invalid uci: {uci!r}")
			return cls(from_square, to_square, ban_piece)
		elif len(uci) == 7 and ":" == uci[6]:
			try:
				from_square = chess.SQUARE_NAMES.index(uci[0:2])
				to_square = chess.SQUARE_NAMES.index(uci[2:4])
				promotion = chess.PIECE_SYMBOLS.index(uci[5])
				ban_piece = chess.PIECE_SYMBOLS.index(uci[7])
			except ValueError:
				raise chess.InvalidMoveError(f"invalid uci: {uci!r}")
			if from_square == to_square:
				raise chess.InvalidMoveError(f"invalid uci (use 0000 for null moves): {uci!r}")
			return cls(from_square, to_square, ban_piece, promotion=promotion)
		else:
			raise chess.InvalidMoveError(f"invalid uci: {uci!r}")

	@classmethod
	def null(cls) -> BessMove:
		return cls(0, 0, None)


class BessBoard(chess.Board):
	move_stack: List[BessMove]

	current_ban: Optional[chess.PieceType] = None

	def reset(self) -> None:
		self.current_ban = None
		super().reset()

	def clear(self) -> None:
		self.current_ban = None
		super().clear()

	def generate_pseudo_legal_moves(self, from_mask: chess.Bitboard = chess.BB_ALL, to_mask: chess.Bitboard = chess.BB_ALL) -> Iterator[BessMove]:
		pm = super().generate_pseudo_legal_moves(from_mask & self.pawns, to_mask)
		nm = super().generate_pseudo_legal_moves(from_mask & self.knights, to_mask)
		bm = super().generate_pseudo_legal_moves(from_mask & self.bishops, to_mask)
		rm = super().generate_pseudo_legal_moves(from_mask & self.rooks, to_mask)
		qm = super().generate_pseudo_legal_moves(from_mask & self.queens, to_mask)
		km = super().generate_pseudo_legal_moves(from_mask & self.kings, to_mask)

		
		if self.current_ban == chess.PAWN:
			moves = itertools.chain(nm, bm, rm, qm ,km)
		elif self.current_ban == chess.KNIGHT:
			moves = itertools.chain(pm, bm, rm, qm, km)
		elif self.current_ban == chess.BISHOP:
			moves = itertools.chain(pm, nm, rm, qm, km)
		elif self.current_ban == chess.ROOK:
			moves = itertools.chain(pm, nm, bm, qm, km)
		elif self.current_ban == chess.QUEEN:
			moves = itertools.chain(pm, nm, bm, rm, km)
		elif self.current_ban == chess.KING:
			moves = itertools.chain(pm, nm, bm, rm, qm)
		elif self.current_ban == None:
			moves = itertools.chain(pm, nm, bm, rm, qm, km)

		for move in moves:
			for piece in chess.PIECE_TYPES:
				yield BessMove(move.from_square, move.to_square, piece, promotion=move.promotion)


	def gives_check(self, move: BessMove) -> bool:
		return super().gives_check(move.move())


class PseudoLegalBessMoveGenerator(chess.PseudoLegalMoveGenerator):
	def __iter__(self) -> Iterator[BessMove]:
		return self.board.generate_pseudo_legal_moves()

	def __contains__(self, move: BessMove) -> bool:
		return self.board.is_pseudo_legal(move.move())

class LegalBessMoveGenerator(chess.LegalMoveGenerator):
	def __iter__(self) -> Iterator[BessMove]:
		return self.board.generate_legal_moves()

	def __contains__(self, move: BessMove) -> bool:
		return self.board.is_legal(move)