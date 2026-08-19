"""
Targeted tests for PersistentVectorIndex's incremental
add/remove/update capabilities, added to support a persistent,
reusable resume corpus index (rather than rebuilding the whole index
per screening request).
"""

import numpy as np
import pytest

from app.infrastructure.vector import PersistentVectorIndex
from app.retrieval.embeddings import ChunkEmbedding


def embedding(chunk_id, resume_id, vector, section="skills"):
    return ChunkEmbedding(
        chunk_id=chunk_id,
        resume_id=resume_id,
        section=section,
        vector=np.asarray(vector, dtype=np.float32),
    )


class TestIncrementalAdd:
    def test_add_to_empty_index_creates_it(self, tmp_path):
        index = PersistentVectorIndex(tmp_path)

        added = index.add(
            [embedding("a-1", "candidate-a", [1.0, 0.0, 0.0])]
        )

        assert added == 1
        assert index.is_built
        assert index.size == 1

    def test_add_appends_without_losing_existing_vectors(
        self, tmp_path
    ):
        index = PersistentVectorIndex(tmp_path)

        index.add(
            [embedding("a-1", "candidate-a", [1.0, 0.0, 0.0])]
        )
        index.add(
            [embedding("b-1", "candidate-b", [0.0, 1.0, 0.0])]
        )

        assert index.size == 2

        results = index.search_chunks(
            np.array([1.0, 0.0, 0.0], dtype=np.float32)
        )
        resume_ids = {result.resume_id for result in results}
        assert resume_ids == {"candidate-a", "candidate-b"}

    def test_adding_the_same_chunk_id_twice_is_not_duplicated(
        self, tmp_path
    ):
        index = PersistentVectorIndex(tmp_path)

        chunk = embedding("a-1", "candidate-a", [1.0, 0.0, 0.0])

        first_added = index.add([chunk])
        second_added = index.add([chunk])

        assert first_added == 1
        assert second_added == 0
        assert index.size == 1

    def test_dimension_mismatch_on_add_is_rejected(self, tmp_path):
        index = PersistentVectorIndex(tmp_path)
        index.add([embedding("a-1", "candidate-a", [1.0, 0.0, 0.0])])

        with pytest.raises(ValueError):
            index.add(
                [embedding("b-1", "candidate-b", [1.0, 0.0])]
            )


class TestRemoveResume:
    def test_remove_deletes_all_of_that_resumes_chunks(
        self, tmp_path
    ):
        index = PersistentVectorIndex(tmp_path)
        index.add(
            [
                embedding("a-1", "candidate-a", [1.0, 0.0, 0.0]),
                embedding(
                    "a-2",
                    "candidate-a",
                    [0.9, 0.1, 0.0],
                    section="experience",
                ),
                embedding("b-1", "candidate-b", [0.0, 1.0, 0.0]),
            ]
        )

        removed = index.remove_resume("candidate-a")

        assert removed == 2
        assert index.size == 1

        results = index.search_chunks(
            np.array([1.0, 0.0, 0.0], dtype=np.float32)
        )
        assert all(
            result.resume_id != "candidate-a" for result in results
        )

    def test_remove_nonexistent_resume_is_a_safe_noop(
        self, tmp_path
    ):
        index = PersistentVectorIndex(tmp_path)
        index.add(
            [embedding("a-1", "candidate-a", [1.0, 0.0, 0.0])]
        )

        removed = index.remove_resume("does-not-exist")

        assert removed == 0
        assert index.size == 1

    def test_remove_on_unbuilt_index_is_a_safe_noop(self, tmp_path):
        index = PersistentVectorIndex(tmp_path)

        assert index.remove_resume("candidate-a") == 0


class TestUpdateResume:
    def test_update_replaces_old_chunks_with_new_ones(
        self, tmp_path
    ):
        index = PersistentVectorIndex(tmp_path)
        index.add(
            [embedding("a-old", "candidate-a", [1.0, 0.0, 0.0])]
        )

        index.update_resume(
            "candidate-a",
            [embedding("a-new", "candidate-a", [0.0, 0.0, 1.0])],
        )

        assert index.size == 1

        results = index.search_chunks(
            np.array([1.0, 0.0, 0.0], dtype=np.float32)
        )
        matching_chunk_ids = {
            result.chunk_id
            for result in results
            if result.resume_id == "candidate-a"
        }
        assert "a-old" not in matching_chunk_ids

    def test_update_does_not_affect_other_resumes(self, tmp_path):
        index = PersistentVectorIndex(tmp_path)
        index.add(
            [
                embedding("a-1", "candidate-a", [1.0, 0.0, 0.0]),
                embedding("b-1", "candidate-b", [0.0, 1.0, 0.0]),
            ]
        )

        index.update_resume(
            "candidate-a",
            [embedding("a-2", "candidate-a", [0.0, 0.0, 1.0])],
        )

        results = index.search_chunks(
            np.array([0.0, 1.0, 0.0], dtype=np.float32)
        )
        assert any(
            result.resume_id == "candidate-b" for result in results
        )


class TestPersistenceAcrossReload:
    def test_incremental_state_survives_save_and_load(
        self, tmp_path
    ):
        original = PersistentVectorIndex(
            tmp_path, model_name="BAAI/bge-m3"
        )
        original.add(
            [embedding("a-1", "candidate-a", [1.0, 0.0, 0.0])]
        )
        original.save()
        original.add(
            [embedding("b-1", "candidate-b", [0.0, 1.0, 0.0])]
        )
        original.save()

        reloaded = PersistentVectorIndex(
            tmp_path, model_name="BAAI/bge-m3"
        )
        reloaded.load()

        assert reloaded.size == 2

        results = reloaded.search_chunks(
            np.array([0.0, 1.0, 0.0], dtype=np.float32)
        )
        resume_ids = {result.resume_id for result in results}
        assert resume_ids == {"candidate-a", "candidate-b"}

    def test_removal_survives_save_and_load(self, tmp_path):
        original = PersistentVectorIndex(tmp_path)
        original.add(
            [
                embedding("a-1", "candidate-a", [1.0, 0.0, 0.0]),
                embedding("b-1", "candidate-b", [0.0, 1.0, 0.0]),
            ]
        )
        original.remove_resume("candidate-a")
        original.save()

        reloaded = PersistentVectorIndex(tmp_path)
        reloaded.load()

        assert reloaded.size == 1
        results = reloaded.search_chunks(
            np.array([0.0, 1.0, 0.0], dtype=np.float32)
        )
        assert all(
            result.resume_id != "candidate-a" for result in results
        )

    def test_try_load_returns_false_when_nothing_persisted(
        self, tmp_path
    ):
        index = PersistentVectorIndex(tmp_path)

        assert index.try_load() is False
        assert not index.is_built

    def test_try_load_returns_true_after_a_save(self, tmp_path):
        original = PersistentVectorIndex(tmp_path)
        original.add(
            [embedding("a-1", "candidate-a", [1.0, 0.0, 0.0])]
        )
        original.save()

        reloaded = PersistentVectorIndex(tmp_path)
        assert reloaded.try_load() is True
        assert reloaded.size == 1


class TestMetadataMapping:
    def test_search_result_metadata_maps_to_correct_chunk(
        self, tmp_path
    ):
        index = PersistentVectorIndex(tmp_path)
        index.add(
            [
                embedding(
                    "exp-2",
                    "resume-42",
                    [1.0, 0.0, 0.0],
                    section="experience",
                ),
            ]
        )

        results = index.search_chunks(
            np.array([1.0, 0.0, 0.0], dtype=np.float32)
        )

        assert results[0].resume_id == "resume-42"
        assert results[0].chunk_id == "exp-2"
        assert results[0].section == "experience"
